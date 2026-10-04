from rest_framework import serializers


class PracticeGenerateSerializer(serializers.Serializer):
    question_id = serializers.IntegerField(required=False, min_value=1)
    upload_id = serializers.IntegerField(required=False, min_value=1)
    question_index = serializers.IntegerField(required=False, min_value=1)
    topic = serializers.CharField(required=False, allow_blank=True)
    problem_type = serializers.CharField(required=False, allow_blank=True)
    difficulty = serializers.ChoiceField(choices=[("easy", "Easy"), ("medium", "Medium"), ("hard", "Hard")], required=False)
    question_text = serializers.CharField(required=False, allow_blank=True)
    concept = serializers.CharField(required=False, allow_blank=True)
    approach = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        has_question_id = data.get("question_id") is not None
        has_upload = data.get("upload_id") is not None
        has_direct = all([data.get("topic"), data.get("problem_type"), data.get("difficulty"), data.get("question_text")])

        if not has_question_id and not has_upload and not has_direct:
            raise serializers.ValidationError(
                "Provide either question_id, or upload_id with question_index, or topic+problem_type+difficulty+question_text."
            )

        if has_upload and data.get("question_index") is None:
            raise serializers.ValidationError("question_index is required when upload_id is provided.")

        if has_question_id and (has_upload or has_direct):
            raise serializers.ValidationError("Provide only one source: question_id, or upload_id+question_index, or direct context.")

        return data
