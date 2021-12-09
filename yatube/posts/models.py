from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.fields import SlugField

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    slug = SlugField(max_length=50, unique=True)

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField('Текст поста',
                            help_text='Введите текст поста')
    pub_date = models.DateTimeField('Дата публикации',
                                    auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор'
    )
    group = models.ForeignKey(Group,
                              related_name='posts',
                              on_delete=models.SET_NULL,
                              blank=True,
                              null=True,
                              verbose_name='Группа',
                              help_text='Выберите группу')

    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ['-pub_date']

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    post = models.ForeignKey(Post,
                             related_name='comments',
                             on_delete=models.CASCADE)
    author = models.ForeignKey(User,
                               related_name='comments',
                               on_delete=models.CASCADE)
    text = models.TextField('Текст комментария',
                            help_text='Введите текст комментария')
    created = models.DateTimeField('Дата публикации',
                                   auto_now_add=True)

    def __str__(self):
        return self.text[:15]


class Follow(models.Model):
    user = models.ForeignKey(User,
                             related_name='follower',
                             on_delete=models.CASCADE)
    author = models.ForeignKey(User,
                               related_name='following',
                               on_delete=models.CASCADE)
