# -*- coding: utf-8 -*-
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class RegisterForm(forms.Form):
    first_name = forms.CharField(label='Имя', max_length=100)
    last_name = forms.CharField(label='Фамилия', max_length=100)
    email = forms.EmailField(label='Email (@appliedtech.ru)')

    first_name.widget.attrs.update({'class': 'form-control'})
    last_name.widget.attrs.update({'class': 'form-control'})
    email.widget.attrs.update({'class': 'form-control'})


class ResultForm(forms.Form):
    set1res1 = forms.IntegerField(label='Результат участника #1 в 1-м сете', max_value=99, min_value=0)
    set1res2 = forms.IntegerField(label='Результат участника #2 в 1-м сете', max_value=99, min_value=0)
    set2res1 = forms.IntegerField(label='Результат участника #1 во 2-м сете', max_value=99, min_value=0)
    set2res2 = forms.IntegerField(label='Результат участника #2 во 2-м сете', max_value=99, min_value=0)
    set3res1 = forms.IntegerField(label='Результат участника #1 в 3-м сете', max_value=99, min_value=0)
    set3res2 = forms.IntegerField(label='Результат участника #2 в 3-м сете', max_value=99, min_value=0)
    set4res1 = forms.IntegerField(label='Результат участника #1 в 4-м сете', max_value=99, min_value=0)
    set4res2 = forms.IntegerField(label='Результат участника #2 в 4-м сете', max_value=99, min_value=0)
    set5res1 = forms.IntegerField(label='Результат участника #1 в 5-м сете', max_value=99, min_value=0)
    set5res2 = forms.IntegerField(label='Результат участника #2 в 5-м сете', max_value=99, min_value=0)

    set1res1.widget.attrs.update({'style': 'max-width: 40px'})
    set1res2.widget.attrs.update({'style': 'max-width: 40px'})
    set2res1.widget.attrs.update({'style': 'max-width: 40px'})
    set2res2.widget.attrs.update({'style': 'max-width: 40px'})
    set3res1.widget.attrs.update({'style': 'max-width: 40px'})
    set3res2.widget.attrs.update({'style': 'max-width: 40px'})
    set4res1.widget.attrs.update({'style': 'max-width: 40px'})
    set4res2.widget.attrs.update({'style': 'max-width: 40px'})
    set5res1.widget.attrs.update({'style': 'max-width: 40px'})
    set5res2.widget.attrs.update({'style': 'max-width: 40px'})

    def clean(self):
        cleaned_data = super().clean()

        for i in range(1, 6):
            f1 = "set{}res1".format(i)
            f2 = "set{}res2".format(i)
            r1 = cleaned_data.get(f1)
            r2 = cleaned_data.get(f2)

            if r1 is None or r2 is None:
                break

            if r1 > r2:
                if r1 - r2 > 2:
                    if r1 != 11:
                        self.add_error(f1, "Set #{}: Result must be 11".format(i))
                elif r1 - r2 == 1:
                    self.add_error(f1, "Set #{}: Point difference must be at least 2".format(i))
                else:
                    if r1 < 11:
                        self.add_error(f1, "Set #{}: Result must be at least 11".format(i))
            elif r2 > r1:
                if r2 - r1 > 2:
                    if r2 != 11:
                        self.add_error(f1, "Set #{}: Result must be 11".format(i))
                elif r2 - r1 == 1:
                    self.add_error(f1, "Set #{}: Point difference must be at least 2".format(i))
                else:
                    if r2 < 11:
                        self.add_error(f1, "Set #{}: Result must be at least 11".format(i))
            else:
                self.add_error(f1, ValidationError(_("Set #{}: Results cannot be equal".format(i))))

        return cleaned_data


class PlayoffResultForm(ResultForm):
    set5res1 = forms.IntegerField(label='Результат участника #1 в 5-м сете', max_value=99, min_value=0, required=False)
    set5res2 = forms.IntegerField(label='Результат участника #2 в 5-м сете', max_value=99, min_value=0, required=False)
    set6res1 = forms.IntegerField(label='Результат участника #1 в 6-м сете', max_value=99, min_value=0, required=False)
    set6res2 = forms.IntegerField(label='Результат участника #2 в 6-м сете', max_value=99, min_value=0, required=False)
    set7res1 = forms.IntegerField(label='Результат участника #1 в 7-м сете', max_value=99, min_value=0, required=False)
    set7res2 = forms.IntegerField(label='Результат участника #2 в 7-м сете', max_value=99, min_value=0, required=False)

    set5res1.widget.attrs.update({'style': 'max-width: 40px'})
    set5res2.widget.attrs.update({'style': 'max-width: 40px'})
    set6res1.widget.attrs.update({'style': 'max-width: 40px'})
    set6res2.widget.attrs.update({'style': 'max-width: 40px'})
    set7res1.widget.attrs.update({'style': 'max-width: 40px'})
    set7res2.widget.attrs.update({'style': 'max-width: 40px'})

    def clean(self):
        cleaned_data = super().clean()

        for i in range(1, 8):
            f1 = "set{}res1".format(i)
            f2 = "set{}res2".format(i)
            r1 = cleaned_data.get(f1)
            r2 = cleaned_data.get(f2)

            if r1 is None or r2 is None:
                break

            if r1 > r2:
                if r1 - r2 > 2:
                    if r1 != 11:
                        self.add_error(f1, "Set #{}: Result must be 11".format(i))
                elif r1 - r2 == 1:
                    self.add_error(f1, "Set #{}: Point difference must be at least 2".format(i))
                else:
                    if r1 < 11:
                        self.add_error(f1, "Set #{}: Result must be at least 11".format(i))
            elif r2 > r1:
                if r2 - r1 > 2:
                    if r2 != 11:
                        self.add_error(f1, "Set #{}: Result must be 11".format(i))
                elif r2 - r1 == 1:
                    self.add_error(f1, "Set #{}: Point difference must be at least 2".format(i))
                else:
                    if r2 < 11:
                        self.add_error(f1, "Set #{}: Result must be at least 11".format(i))
            else:
                self.add_error(f1, ValidationError(_("Set #{}: Results cannot be equal".format(i))))


class UserCreationForm(forms.ModelForm):
    """
    A form that creates a user, with no privileges, from the given username and
    password.
    """
    error_messages = {
        'password_mismatch': _("The two password fields didn't match."),
    }
    password1 = forms.CharField(label=_("Password"), widget=forms.PasswordInput)
    password2 = forms.CharField(label=_("Password confirmation"), widget=forms.PasswordInput,
                                help_text=_("Enter the same password as above, for verification."))

    password1.widget.attrs.update({'class': 'form-control'})
    password2.widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name")
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(UserCreationForm, self).__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        return password2

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user
