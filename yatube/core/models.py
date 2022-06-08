from django.db import models

LETTERS_IN_STR: int = 15


class CreatedModel(models.Model):
    """Абстрактная модель. Добавляет дату создания,
    сортировку и строку.
    """
    pub_date = models.DateTimeField(
        'Дата создания',
        auto_now_add=True
    )

    class Meta:
        abstract = True
        ordering = ['-pub_date']

    def __str__(self) -> str:
        return self.text[:LETTERS_IN_STR]
