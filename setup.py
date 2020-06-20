import setuptools
from batch_textures_convert import version

with open("README.md", "r") as f:
    readme = f.read()

setuptools.setup(
    name="batch_textures_convert",
    version=version.__version__,
    author="Juraj Tomori",
    author_email="jtomori@pm.me",
    description="Batch convert textures to various render-friendly mip-mapped formats",
    long_description=readme,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(exclude=["tests"]),
    python_requires=">=3.6",
    zip_safe=False
)
