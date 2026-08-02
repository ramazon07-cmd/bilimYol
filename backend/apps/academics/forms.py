from django import forms


class MathAnswerKeyCsvUploadForm(forms.Form):
    csv_file = forms.FileField(
        label="Matematika javoblari CSV fayli",
        help_text="Faqat .csv formatidagi faylni yuklang.",
    )

    def clean_csv_file(self):
        csv_file = self.cleaned_data["csv_file"]

        if not csv_file.name.lower().endswith(".csv"):
            raise forms.ValidationError("Faqat CSV fayl yuklash mumkin.")

        if csv_file.size > 5 * 1024 * 1024:
            raise forms.ValidationError("CSV fayl 5 MB dan katta bo‘lmasligi kerak.")

        return csv_file