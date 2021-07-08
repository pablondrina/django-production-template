from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save

from apps.accounts.models import User
from apps.places.models import Address


# @receiver(pre_save, sender=Address)
# def update_m2m_relationships_on_save(sender, instance, **kwargs):
    # print(f"\n\n{instance}\n\n")
    # instance.formset.save()  # this will save the children
    # instance.save()  # form.instance is the parent

#TODO ACESSAR FORMSET POR AQUI
# o OBJETIVO É APENAS ATUALIZAR OS CAMPOS DE ENDEREÇO, SEMPRE QUE O CAMPO 'LOCATION' FOR ALTERADO.

    # if instance.formset.has_changed():
    #     print('ok')

    # if instance.addresses:
    #     a = instance.addresses.last()
    #     print(f'Peguei o último endereço: {a.id}')
    #     instance.add_address(a.id)
    #     print('Peguei o id dele')
