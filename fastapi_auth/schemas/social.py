from datetime import datetime
from typing import Union

from pydantic import BaseModel, EmailStr, HttpUrl


class GithubPlan(BaseModel):
    collaborators: int
    name: str
    space: int
    private_repos: int


class GithubPublicUser(BaseModel):
    login: str
    id: int
    user_view_type: str | None = None
    node_id: str
    avatar_url: HttpUrl
    gravatar_id: str | None
    url: HttpUrl
    html_url: HttpUrl
    followers_url: HttpUrl
    following_url: str
    gists_url: str
    starred_url: str
    subscriptions_url: HttpUrl
    organizations_url: HttpUrl
    repos_url: HttpUrl
    events_url: str
    received_events_url: HttpUrl
    type: str
    site_admin: bool
    name: str | None
    company: str | None
    blog: str | None
    location: str | None
    email: EmailStr | None
    notification_email: EmailStr | None = None
    hireable: bool | None
    bio: str | None
    twitter_username: str | None = None
    public_repos: int
    public_gists: int
    followers: int
    following: int
    created_at: datetime
    updated_at: datetime
    plan: GithubPlan | None = None
    private_gists: int | None = None
    total_private_repos: int | None = None
    owned_private_repos: int | None = None
    disk_usage: int | None = None
    collaborators: int | None = None


class GithubPrivateUser(BaseModel):
    login: str
    id: int
    user_view_type: str | None = None
    node_id: str
    avatar_url: HttpUrl
    gravatar_id: str | None
    url: HttpUrl
    html_url: HttpUrl
    followers_url: HttpUrl
    following_url: str
    gists_url: str
    starred_url: str
    subscriptions_url: HttpUrl
    organizations_url: HttpUrl
    repos_url: HttpUrl
    events_url: str
    received_events_url: HttpUrl
    type: str
    site_admin: bool
    name: str | None
    company: str | None
    blog: str | None
    location: str | None
    email: EmailStr | None
    notification_email: EmailStr | None = None
    hireable: bool | None
    bio: str | None
    twitter_username: str | None = None
    public_repos: int
    public_gists: int
    followers: int
    following: int
    created_at: datetime
    updated_at: datetime
    private_gists: int
    total_private_repos: int
    owned_private_repos: int
    disk_usage: int
    collaborators: int
    two_factor_authentication: bool
    plan: GithubPlan | None = None
    business_plus: bool | None = None
    ldap_dn: str | None = None


GithubUserResponse = Union[GithubPublicUser, GithubPrivateUser]
