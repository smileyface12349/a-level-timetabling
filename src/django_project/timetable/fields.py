from django.forms import ModelChoiceField

from .models import User


class CustomModelChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        example_student = User.objects.filter(link__group_id__id__exact=obj.id, user_type='student')[:1]
        if example_student:
            example_student = example_student.get()
        if example_student and example_student.year_group:
            text = f"{example_student.year_group} - {obj.name}"
        else:
            text = obj.name
        return text