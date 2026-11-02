# Berlin Imports

Django storefront foundation for an automotive spare-parts retailer. The existing `berlin` Django project module is retained; the application is split into focused apps as features are added.

## Project structure

```text
berlin/
├── accounts/       # Customer accounts and profile
├── cart/           # Shopping cart
├── catalog/        # Brands, categories, products, and fitment
├── core/           # Home page and shared site pages
├── orders/         # Checkout and order history
├── payments/       # Payment service and provider callbacks
├── berlin/         # Django settings and root URLs
├── static/         # Tailwind source and generated CSS
├── templates/      # Shared and core templates
├── manage.py
├── package.json
└── requirements.txt
```

Inventory is planned as part of `catalog` initially to keep stock rules close to products. Payment provider, currency, delivery markets and fees, returns policy, and checkout account requirements remain open business decisions; no payment integration or commercial policy is configured in this foundation.

## Local setup

From this directory, create and activate a virtual environment if you do not already have one, then install the Python dependencies:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`.

Create a local environment file and replace the example secret with a generated development key:

```sh
cp .env.example .env
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Put the generated value in `.env` as `SECRET_KEY`. Do not commit `.env`; production secrets must be supplied through the deployment environment.

Install the JavaScript build dependencies and compile Tailwind CSS:

```sh
npm ci
npm run css:build
```

For development, use `npm run css:watch` in a separate terminal while running Django.

Initialize the local database and start the development server:

```sh
python manage.py migrate
python manage.py runserver
```

Visit <http://127.0.0.1:8000/>. Django uses SQLite locally by default. To use PostgreSQL, set `DATABASE_URL` to a PostgreSQL connection URL in `.env`; the PostgreSQL driver is included. `DEBUG`, `ALLOWED_HOSTS`, and `CSRF_TRUSTED_ORIGINS` are also configurable through environment variables.

Run the automated tests and Django checks with:

```sh
python manage.py test
python manage.py check
```

## Phase 1 status

The shared responsive template, environment-based settings, modular Django app skeletons, and Tailwind CLI build are in place.

## Phase 2 status

The catalogue includes brands, categories, products, images, and vehicle fitment, with staff management in Django admin. The storefront supports catalogue, brand, and category listings; search by product/vehicle terms; vehicle, price, currency, and stock filters; sorting; pagination; and product detail pages. Development seed data includes the four requested vehicle brands and initial categories, including the owner-confirmed “Engine management and control units” wording. No example product data or images are fabricated.

## Phase 3: accounts and cart

Customer registration, login, POST-only logout, password reset, and a private customer profile are available under `/accounts/`. The profile stores contact and delivery details. Development password reset emails are written to the console; configure SMTP through environment variables in production.

The cart is available at `/cart/`. Guests keep their cart in the Django session. Authenticated customers have a private database cart, and the guest cart is merged on login; merged quantities are limited to current stock and unavailable products are skipped. Prices and totals are read and calculated server-side. If the catalogue contains more than one currency, the cart displays a separate subtotal per currency; it never converts or adds different currencies. Checkout and payment are not implemented in this phase.

To populate the empty development catalogue with conspicuously labelled sample products, pass a currency code explicitly:

```sh
python manage.py seed_demo_catalogue --currency XXX
```

`XXX` is the ISO 4217 no-currency code, used here to avoid assuming the store's actual currency. Sample product names and prices are for local testing only, not approved listings. You can instead provide a confirmed code in your local development environment when running the command. No demo customer or password is created.

The current local development database has a `devadmin` superuser with a generated password that was not displayed. Set a password you choose before using the admin:

```sh
python manage.py changepassword devadmin
```

For a fresh database, create an administrator interactively with `python manage.py createsuperuser`.

## Production environment and static/media files

Production settings require `DEBUG=false`, a PostgreSQL `DATABASE_URL`, a strong `SECRET_KEY`, appropriate `ALLOWED_HOSTS`, and `CSRF_TRUSTED_ORIGINS` for the deployment's HTTPS origin. Set SMTP values using `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS` or `EMAIL_USE_SSL`, and `DEFAULT_FROM_EMAIL`. Keep all credentials in the deployment environment, never in source control. HTTPS redirects and secure session/CSRF cookies are enabled when debug mode is off; configure the reverse proxy to terminate TLS and pass requests securely.

Run `python manage.py collectstatic` during deployment and serve `STATIC_ROOT` through the reverse proxy or a static-file service. `MEDIA_ROOT` contains uploaded product images; persist it on a separate deployment volume or configure object storage in production. Do not mount the SQLite development database or local uploads into a public web root. This project is environment-configurable and ready to be containerized later, but does not include Docker, CI/CD, or Tailscale automation.

## Git

The project is tracked from the workspace root. `.gitignore` excludes environment files, local databases, virtual environments, uploaded media, build output, and editor/OS files. `.env.example` contains placeholders only. No GitHub remote is configured; do not push until the intended repository and remote are confirmed.
