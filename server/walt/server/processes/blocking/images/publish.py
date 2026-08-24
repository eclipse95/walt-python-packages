from __future__ import annotations

import typing

from walt.server.processes.blocking.images.metadata import (
    update_user_metadata_for_image,
)
from walt.server.processes.blocking.registries import (
    MissingRegistryCredentials,
    get_registry_client,
)

if typing.TYPE_CHECKING:
    from walt.server.processes.main.server import Server


# this implements walt image publish
def publish(requester, server: Server, registry_label, image_fullname, **kwargs):
    try:
        registry = get_registry_client(requester, registry_label)
        # push image
        success = registry.push(requester, image_fullname)
        # if hub, update user metadata ('walt_metadata' image on user's hub account)
        if registry_label == "hub":
            if success:
                labels = server.images.store[image_fullname].get_labels()
                update_user_metadata_for_image(
                    requester, registry, image_fullname, labels
                )
    except MissingRegistryCredentials as e:
        return ("MISSING_REGISTRY_CREDENTIALS", e.registry_label)
    except Exception:
        requester.stderr.write(
            f"Failed to communicate with {registry_label} registry. Aborted.\n"
        )
        return ("FAILED",)
    if success:
        clone_url = registry.get_origin_clone_url(requester, image_fullname)
        clone_url = clone_url.removesuffix(":latest")
        return ("OK", clone_url)
    return ("FAILED",)
