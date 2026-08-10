from pathlib import Path


class Base:
    DEFAULT_MAX_ITERATIONS = 25
    DEFAULT_MAX_OUTPUT_TOKENS = 1024

    @classmethod
    def task_name(cls):
        raise NotImplementedError(f"{cls.__name__} must define .task_name()")

    @classmethod
    def provider(cls, settings):
        value = _fetch(settings, "provider")
        if value is None:
            raise ValueError(f"tasks.{cls.task_name()}.provider is required in settings.yaml")
        return value

    @classmethod
    def model(cls, settings):
        value = _fetch(settings, "model")
        if value is None:
            raise ValueError(f"tasks.{cls.task_name()}.model is required in settings.yaml")
        return value

    @classmethod
    def prompt_override(cls, settings, prompt="system"):
        node = _fetch(settings, "prompt_override")
        if not isinstance(node, dict):
            return False
        return node.get(str(prompt)) is True

    @classmethod
    def prompt(cls, settings, name="system", user_prompts_dir=None, default_prompts_dir=None):
        if cls.prompt_override(settings, name):
            text = cls._read_user_prompt(name, user_prompts_dir=user_prompts_dir)
            if text is not None:
                return text

        return cls._read_default_prompt(name, default_prompts_dir=default_prompts_dir)

    @classmethod
    def system_prompt(cls, settings, user_prompts_dir=None, default_prompts_dir=None):
        return cls.prompt(
            settings,
            "system",
            user_prompts_dir=user_prompts_dir,
            default_prompts_dir=default_prompts_dir,
        )

    @classmethod
    def max_iterations(cls, settings):
        return _integer_setting(settings, "max_iterations", cls.DEFAULT_MAX_ITERATIONS)

    @classmethod
    def max_output_tokens(cls, settings):
        return _integer_setting(settings, "max_output_tokens", cls.DEFAULT_MAX_OUTPUT_TOKENS)

    # ---------- private ---------------------------------------------------

    @classmethod
    def _read_user_prompt(cls, prompt_name, user_prompts_dir=None):
        if user_prompts_dir is None:
            return None
        return _read_file(Path(user_prompts_dir) / cls.task_name() / f"{prompt_name}.md")

    @classmethod
    def _read_default_prompt(cls, prompt_name, default_prompts_dir=None):
        if default_prompts_dir is None:
            return None
        return _read_file(Path(default_prompts_dir) / f"{prompt_name}.md")


def _fetch(settings, key):
    if not isinstance(settings, dict):
        return None
    return settings.get(str(key))


def _integer_setting(settings, key, default):
    value = _fetch(settings, key)
    if value is None:
        return default
    return int(value)


def _read_file(path):
    path = Path(path)
    return path.read_text().strip() if path.exists() else None
