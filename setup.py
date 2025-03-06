from setuptools import setup, find_packages

setup(
    name="grok-client",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "playwright>=1.40.0",
    ],
    python_requires=">=3.7",
    description="A Python client for Grok chat",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/grok-chat",
) 