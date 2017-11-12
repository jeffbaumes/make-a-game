from twisted.protocols import amp


class GetChunk(amp.Command):
    arguments = [(b'x', amp.Integer()),
                 (b'y', amp.Integer())]
    response = [(b'chunk', amp.Unicode())]


class UpdateChunk(amp.Command):
    arguments = [(b'chunk', amp.Unicode())]
    response = [(b'result', amp.Boolean())]


class UpdateMaterial(amp.Command):
    arguments = [(b'x', amp.Integer()),
                 (b'y', amp.Integer()),
                 (b'material', amp.Integer())]
    response = [(b'result', amp.Boolean())]


class UpdateUserPosition(amp.Command):
    arguments = [(b'user', amp.Unicode()),
                 (b'x', amp.Float()),
                 (b'y', amp.Float())]
    response = [(b'result', amp.Boolean())]
