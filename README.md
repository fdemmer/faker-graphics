# faker-graphics

[![CI](https://github.com/fdemmer/faker-graphics/actions/workflows/test.yml/badge.svg)](https://github.com/fdemmer/faker-graphics/actions/workflows/test.yml)
[![Version](https://img.shields.io/pypi/v/faker-graphics.svg)](https://pypi.org/project/faker-graphics/)
[![Python](https://img.shields.io/pypi/pyversions/faker-graphics.svg)](https://pypi.org/project/faker-graphics/)
[![License](https://img.shields.io/pypi/l/faker-graphics.svg)](https://pypi.org/project/faker-graphics/)

Provider for [Faker](https://pypi.org/project/Faker/) to generate placeholder images with [cairo](https://www.cairographics.org).

- Includes a random color generator forked from the
  [Python port](https://github.com/kevinwuhoo/randomcolor-py) of
  [randomColor.js](https://github.com/davidmerfield/randomColor)
- Provides a simple CLI to generate image files or just colors in the terminal
- Generated images show size, aspect ratio and a simple geometry

## Installation

```bash
$ pip install faker-graphics
```

## Setup

### Register the provider with Faker

The faker-graphics provider will reuse Faker's random instance.

```python
from faker import Faker
from faker_graphics import Provider

fake = Faker()
fake.add_provider(Provider)
```

### Register the provider with Faker via Factory-Boy

```python
import factory
from faker_graphics import Provider

factory.Faker.add_provider(Provider)
```

# Examples

### Use with Factory-Boy/Django

```python
import factory

class ModelWithImageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'models.ModelWithImage'

    image = factory.django.FileField(
        filename='mock_image.png',
        data=factory.Faker(
            'placeholder_image',
            width=640,
            height=480,
            hue='green',
            luminosity='dark',
        ),
    )

```

### Generate an image via CLI

```bash
$ python -m faker_graphics png sample.png --size 640 480 green --luminosity dark
```

Use `--help` to see all options.

### Example Image

![Example Image](https://raw.githubusercontent.com/fdemmer/faker-graphics/main/docs/img/example.png)
