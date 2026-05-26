from django.db import migrations, models


def copy_role_to_user(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    Role = apps.get_model('accounts', 'Role')

    role_map = {
        'principal': 'admin',
        'head': 'head',
        'teacher': 'manager',
        'staff': 'staff',
        'student': 'staff',
        'parent': 'staff',
    }

    for old_role in Role.objects.all():
        new_role = role_map.get(old_role.role, 'staff')
        User.objects.filter(pk=old_role.user_id).update(role=new_role)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user',
            old_name='full_name',
            new_name='fullname',
        ),
        migrations.AddField(
            model_name='user',
            name='username',
            field=models.CharField(blank=True, max_length=50, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[
                    ('admin', 'Admin'),
                    ('head', 'Head'),
                    ('manager', 'Manager'),
                    ('staff', 'Staff'),
                ],
                default='staff',
                max_length=20,
            ),
        ),
        migrations.RunPython(copy_role_to_user, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='user',
            name='phone',
        ),
        migrations.AlterField(
            model_name='user',
            name='is_active',
            field=models.BooleanField(
                default=False,
                help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.',
                verbose_name='active',
            ),
        ),
        migrations.DeleteModel(
            name='Role',
        ),
    ]
