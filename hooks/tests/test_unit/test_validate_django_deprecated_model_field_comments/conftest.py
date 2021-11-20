from __future__ import annotations

MULTI_LINE_FOREIGN_KEY_WITH_LEADING_COMMENT = """
article = models.ForeignKey(  # null_for_compatibility
    to='Article',
    null=True,
    on_delete=models.PROTECT
)
"""

MULTI_LINE_ANNOTATED_FOREIGN_KEY_WITH_LEADING_COMMENT = """
article: Article = models.ForeignKey(  # null_for_compatibility
    to='Article',
    null=True,
    on_delete=models.PROTECT
)
"""

MULTI_LINE_FOREIGN_KEY_WITH_LEADING_COMMENTS = """
article = models.ForeignKey(  # null_for_compatibility # allowed_cascade
    to='Article',
    null=True,
    on_delete=models.CASCADE
)
"""

MULTI_LINE_ANNOTATED_FOREIGN_KEY_WITH_LEADING_COMMENTS = """
article: Article = models.ForeignKey(  # null_for_compatibility # allowed_cascade
    to='Article',
    null=True,
    on_delete=models.CASCADE
)
"""

MULTI_LINE_FOREIGN_KEY_WITH_TRAILING_COMMENT = """
article = models.ForeignKey(
    to='Article',
    null=True,
    on_delete=models.PROTECT
)  # null_for_compatibility
"""

MULTI_LINE_ANNOTATED_FOREIGN_KEY_WITH_TRAILING_COMMENT = """
article: Article = models.ForeignKey(
    to='Article',
    on_delete=models.PROTECT
)  # whatever
"""

MULTI_LINE_FOREIGN_KEY_WITH_TRAILING_COMMENTS = """
article = models.ForeignKey(
    to='Article',
    null=True,
    on_delete=models.CASCADE
)  # null_for_compatibility # allowed_cascade
"""

MULTI_LINE_ANNOTATED_FOREIGN_KEY_WITH_TRAILING_COMMENTS = """
article: Article = models.ForeignKey(
    to='Article',
    null=True,
    on_delete=models.CASCADE
)  # null_for_compatibility # allowed_cascade
"""

MULTI_LINE_FOREIGN_KEY_WITHOUT_COMMENTS = """
article = models.ForeignKey(
    to='Article',
    on_delete=models.PROTECT
)
"""

MULTI_LINE_ANNOTATED_FOREIGN_KEY_WITHOUT_COMMENTS = """
article: Article = models.ForeignKey(
    to='Article',
    on_delete=models.PROTECT
)
"""

ONE_LINE_FOREIGN_KEY_WITH_TRAILING_COMMENT = """
article = models.ForeignKey(to='Article', null=True) # null_for_compatibility
"""

ONE_LINE_ANNOTATED_FOREIGN_KEY_WITH_TRAILING_COMMENT = """
article: Article = models.ForeignKey(to='Article', null=True) # null_for_compatibility
"""

ONE_LINE_FOREIGN_KEY_WITH_TRAILING_COMMENTS = """
article = models.ForeignKey(to='Article', null=True) # null_for_compatibility # deprecated SMTH-100500 20.09.2021
"""

ONE_LINE_ANNOTATED_FOREIGN_KEY_WITH_TRAILING_COMMENTS = """
article: Article = models.ForeignKey(to='Article', null=True) # null_by_design # deprecated SMTH-100500 20.09.2021
"""

ONE_LINE_FIELD_WITHOUT_COMMENTS = """
first_name = models.CharField()
"""

ONE_LINE_ANNOTATED_FIELD_WITHOUT_COMMENTS = """
first_name: str = models.CharField()
"""

ONE_LINE_FIELD_WITH_TRAILING_COMMENT = """
first_name = models.CharField(null=True) # null_for_compatibility
"""

ONE_LINE_ANNOTATED_FIELD_WITH_TRAILING_COMMENT = """
first_name: str = models.CharField(null=True) # null_for_compatibility
"""

ONE_LINE_FIELD_WITH_TRAILING_COMMENTS = """
first_name = models.CharField(null=True) # null_for_compatibility # deprecated SMTH-100500 20.09.2021
"""

ONE_LINE_ANNOTATED_FIELD_WITH_TRAILING_COMMENTS = """
first_name: str = models.CharField(null=True) # null_for_compatibility # deprecated SMTH-100500 20.09.2021
"""

MULTI_LINE_FOREIGN_KEY_WITH_LEADING_AND_TRAILING_COMMENTS = """
article = models.ForeignKey(  # null_for_compatibility # allowed_cascade
    to='Article',
    null=True,
    on_delete=models.CASCADE
)  # deprecated SMTH-100500 20.09.2021
"""

MULTI_LINE_ANNOTATED_FOREIGN_KEY_WITH_LEADING_AND_TRAILING_COMMENTS = """
article: Article = models.ForeignKey(  # deprecated SMTH-100500 20.09.2021
    to='Article',
    null=True,
    on_delete=models.CASCADE
)  # null_for_compatibility # allowed_cascade
"""

MULTI_LINE_FIELD_WITH_LEADING_AND_TRAILING_COMMENTS = """
first_name = models.CharField(  # null_for_compatibility
    null=True,
    verbose_name='Имя',
    help_text='Имя пользователя',
)  # deprecated SMTH-100500 20.09.2021
"""

MULTI_LINE_ANNOTATED_FIELD_WITH_LEADING_AND_TRAILING_COMMENTS = """
first_name: str = models.CharField(  # null_for_compatibility
    null=True,
    verbose_name='Имя',
    help_text='Имя пользователя',
)  # deprecated SMTH-100500 20.09.2021
"""
