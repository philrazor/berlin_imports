from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import CustomerProfile

User = get_user_model()


class AccountTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='customer',
            email='customer@example.test',
            password='Secure-test-password-42!',
            first_name='Taylor',
            last_name='Customer',
        )
        self.profile = CustomerProfile.objects.create(
            user=self.user,
            phone='+1 555 0100',
            address_line_1='12 Sample Street',
            city='Berlin',
            country='Germany',
        )

    def test_registration_creates_user_and_profile_and_logs_in(self):
        response = self.client.post(
            reverse('accounts:register'),
            {
                'username': 'new-customer',
                'email': 'new@example.test',
                'first_name': 'New',
                'last_name': 'Customer',
                'phone': '+49 30 123456',
                'password1': 'Other-secure-password-43!',
                'password2': 'Other-secure-password-43!',
            },
        )

        self.assertRedirects(response, reverse('accounts:profile'))
        new_user = User.objects.get(username='new-customer')
        self.assertTrue(new_user.check_password('Other-secure-password-43!'))
        self.assertEqual(new_user.customer_profile.phone, '+49 30 123456')
        self.assertEqual(int(self.client.session['_auth_user_id']), new_user.pk)

    def test_registration_rejects_case_insensitive_duplicate_email(self):
        response = self.client.post(
            reverse('accounts:register'),
            {
                'username': 'duplicate',
                'email': 'CUSTOMER@example.test',
                'first_name': 'Duplicate',
                'last_name': 'Email',
                'password1': 'Other-secure-password-43!',
                'password2': 'Other-secure-password-43!',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'An account with this email address already exists.')
        self.assertFalse(User.objects.filter(username='duplicate').exists())

    def test_login_and_post_logout(self):
        response = self.client.post(
            reverse('accounts:login'),
            {'username': 'customer', 'password': 'Secure-test-password-42!'},
        )
        self.assertRedirects(response, reverse('accounts:profile'))
        self.assertTrue(response.wsgi_request.user.is_authenticated)

        response = self.client.post(reverse('accounts:logout'))
        self.assertRedirects(response, reverse('core:home'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_does_not_accept_get(self):
        response = self.client.get(reverse('accounts:logout'))

        self.assertEqual(response.status_code, 405)

    def test_profile_requires_authentication(self):
        response = self.client.get(reverse('accounts:profile'))

        self.assertRedirects(
            response,
            f'{reverse("accounts:login")}?next={reverse("accounts:profile")}',
        )

    def test_profile_updates_only_the_authenticated_user(self):
        other_user = User.objects.create_user(
            username='other',
            email='other@example.test',
            password='Another-secure-password-44!',
        )
        other_profile = CustomerProfile.objects.create(
            user=other_user,
            city='Other City',
        )
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('accounts:profile'),
            {
                'first_name': 'Updated',
                'last_name': 'Name',
                'email': 'updated@example.test',
                'phone': '+49 30 777777',
                'address_line_1': '34 New Road',
                'address_line_2': '',
                'city': 'Berlin',
                'region': '',
                'postal_code': '10115',
                'country': 'Germany',
            },
        )

        self.assertRedirects(response, reverse('accounts:profile'))
        self.user.refresh_from_db()
        self.profile.refresh_from_db()
        other_profile.refresh_from_db()
        self.assertEqual(self.user.email, 'updated@example.test')
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.profile.address_line_1, '34 New Road')
        self.assertEqual(other_profile.city, 'Other City')

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_password_reset_flow_completes(self):
        response = self.client.post(
            reverse('accounts:password_reset'),
            {'email': self.user.email},
        )
        self.assertRedirects(response, reverse('accounts:password_reset_done'))
        self.assertEqual(len(mail.outbox), 1)

        reset_url = mail.outbox[0].body.splitlines()[3]
        response = self.client.get(reset_url)
        self.assertEqual(response.status_code, 302)
        reset_url = response['Location']
        response = self.client.post(
            reset_url,
            {
                'new_password1': 'Brand-new-secure-password-45!',
                'new_password2': 'Brand-new-secure-password-45!',
            },
        )

        self.assertRedirects(response, reverse('accounts:password_reset_complete'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('Brand-new-secure-password-45!'))

    def test_profile_email_must_remain_unique(self):
        User.objects.create_user(
            username='other',
            email='other@example.test',
            password='Another-secure-password-44!',
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('accounts:profile'),
            {
                'first_name': 'Taylor',
                'last_name': 'Customer',
                'email': 'OTHER@example.test',
                'phone': '',
                'address_line_1': '',
                'address_line_2': '',
                'city': '',
                'region': '',
                'postal_code': '',
                'country': '',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'An account with this email address already exists.')
