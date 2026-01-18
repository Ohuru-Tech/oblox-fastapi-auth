from fastapi_auth.models.social_providers import SupportedProviders

from .github import GithubSocialProvider

provider_maps = {
    SupportedProviders.GITHUB: GithubSocialProvider,
}
