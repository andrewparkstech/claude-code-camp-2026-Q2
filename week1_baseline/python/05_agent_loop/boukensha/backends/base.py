from ..errors import UnsupportedModelError


class Base:
    @classmethod
    def models(cls):
        models = getattr(cls, "MODELS", None)
        if models is None:
            raise NotImplementedError(f"{cls.__name__} must define MODELS")
        return models

    @classmethod
    def model_info_for(cls, model):
        return cls.models().get(str(model))

    @classmethod
    def validate_model(cls, model):
        model = str(model)
        if cls.model_info_for(model):
            return model

        supported = ", ".join(sorted(cls.models().keys()))
        raise UnsupportedModelError(
            f"{cls.__name__} does not support model {model!r}. Supported models: {supported}"
        )

    @property
    def context_window(self):
        return self.model_info["context_window"]

    @property
    def input_token_cost_per_million(self):
        return self.model_info["cost_per_million"]["input"]

    @property
    def output_token_cost_per_million(self):
        return self.model_info["cost_per_million"]["output"]

    @property
    def usage_unit(self):
        return self.model_info["usage_unit"]

    @property
    def usage_level(self):
        return self.model_info.get("usage_level")

    def estimate_cost(self, input_tokens, output_tokens):
        if self.input_token_cost_per_million is None or self.output_token_cost_per_million is None:
            return None

        return (
            (input_tokens * self.input_token_cost_per_million)
            + (output_tokens * self.output_token_cost_per_million)
        ) / 1_000_000.0

    # ---------- private ---------------------------------------------------

    def _configure_model(self, model):
        self.model = self.validate_model(model)
        self.model_info = self.model_info_for(self.model)
