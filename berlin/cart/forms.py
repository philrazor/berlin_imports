from django import forms


class CartQuantityForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, max_value=1000)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['quantity'].widget.attrs.update(
            {
                'class': 'w-24 rounded-md border border-slate-300 px-3 py-2',
                'min': 1,
                'max': 1000,
            }
        )
