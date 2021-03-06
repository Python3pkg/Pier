
from contextlib import contextmanager
from distutils.util import strtobool
from uuid import uuid4
import json
import platform

from characteristic import Attribute, attributes
from docker.client import Client
from docker.errors import APIError
from docker.utils import kwargs_from_env


if platform.system() == "Darwin":
    CLIENT_DEFAULTS = kwargs_from_env(assert_hostname=False)
else:
    CLIENT_DEFAULTS = {}


class ImageBuildFailure(Exception):
    pass


def client_from_opts(client_opts=()):
    """
    Construct a docker-py Client from a string specifying options.

    """

    kwargs = CLIENT_DEFAULTS.copy()

    for name, value in client_opts:
        if name == "timeout":
            kwargs["timeout"] = int(value)
        elif name == "tls":
            kwargs["tls"] = strtobool(value.lower())
        else:
            kwargs[name] = value

    return Client(**kwargs)


@attributes([Attribute(name="client", default_factory=client_from_opts)])
class Docker(object):
    @contextmanager
    def temporary_image(self, context=None, forcerm=True, **kwargs):
        if context is not None:
            kwargs.update(custom_context=True, fileobj=context)

        image = Image(client=self.client)
        yield image.build(rm=True, forcerm=forcerm, **kwargs)

        try:
            image.remove()
        except APIError:
            pass


@attributes(
    [
        Attribute(name="image"),
        Attribute(name="log", default_value=()),
        Attribute(name="error", default_value=None),
    ],
)
class Build(object):
    """
    An image build.

    """

    @classmethod
    def run(cls, image, client, **kwargs):
        error, log = None, []
        for event in client.build(tag=image.id, **kwargs):
            try:
                log.append(_parse_API_event(event))
            except ImageBuildFailure as exception:
                error = str(exception)
        return cls(image=image, log=log, error=error)


def _parse_API_event(event_json):
    event = json.loads(event_json)
    error = event.get("errorDetail")
    if error is not None:
        message = error.pop("message")
        assert not error, error
        raise ImageBuildFailure(message)
    elif list(event.keys()) != ["stream"]:
        raise ImageBuildFailure(event)
    else:
        return event["stream"]


@attributes(
    [
        Attribute(name="id", default_factory=lambda : uuid4().hex),
        Attribute(name="client"),
    ],
)
class Image(object):
    @contextmanager
    def temporary_container(self, **kwargs):
        container = Container.create(
            client=self.client, image=self.id, **kwargs
        )
        yield container
        container.remove()

    def build(self, **kwargs):
        return Build.run(image=self, client=self.client, **kwargs)

    def remove(self):
        self.client.remove_image(self.id)


@attributes(
    [
        Attribute(name="id"),
        Attribute(name="client"),
        Attribute(name="volumes", default_value=()),
    ],
)
class Container(object):
    @classmethod
    def create(cls, client, volumes=(), **kwargs):
        response = client.create_container(**kwargs)
        return cls(id=response["Id"], client=client, volumes=volumes)

    def remove(self):
        self.client.stop(container=self.id)
        self.client.remove_container(self.id)

    def start(self, **kwargs):
        if "binds" in kwargs:
            raise TypeError(
                "Volumes should be specified as instances of Volume",
            )
        self.client.start(
            container=self.id,
            binds=dict(volume.to_bind() for volume in self.volumes),
            **kwargs
        )

    def logs(self, stream=True, **kwargs):
        return self.client.logs(container=self.id, stream=stream, **kwargs)

    def wait(self, **kwargs):
        return self.client.wait(container=self.id, **kwargs)


@attributes(
    [
        Attribute(name="bind"),
        Attribute(name="mount_point"),
        Attribute(name="read_only", default_value=False),
    ],
)
class Volume(object):
    def to_bind(self):
        return (
            self.bind.path, {"bind" : self.mount_point, "ro" : self.read_only}
        )
