# OPA/Rego Authorization Policies for LLM Security Gateway
# Defines who can access which models and perform which actions

package llm.authz

import future.keywords.if
import future.keywords.in

# Default deny
default allow = false

# Admin users have full access
allow if {
    input.user.role == "admin"
}

# Users can access models based on their tier
allow if {
    input.user.role == "user"
    input.action == "chat"
    model_allowed_for_tier(input.user.tier, input.resource.model)
}

# Model access by tier
model_allowed_for_tier("free", model) if {
    model in ["gpt-3.5-turbo", "local"]
}

model_allowed_for_tier("premium", model) if {
    model in ["gpt-3.5-turbo", "claude-3-sonnet", "local"]
}

model_allowed_for_tier("enterprise", model) if {
    model in [
        "gpt-3.5-turbo",
        "gpt-4",
        "claude-3-sonnet",
        "claude-3-opus",
        "local"
    ]
}

# Service accounts can access specific models
allow if {
    input.user.role == "service"
    input.user.service_name in allowed_services
}

allowed_services := ["mcp-control-plane", "ci-cd-pipeline"]

# Get user permissions
permissions := {
    "allowed_models": allowed_models_for_user,
    "allowed_actions": allowed_actions_for_user,
    "rate_limits": rate_limits_for_user,
} if {
    input.user
}

# Calculate allowed models for user
allowed_models_for_user := models if {
    input.user.role == "admin"
    models := ["*"]
}

allowed_models_for_user := models if {
    input.user.role == "user"
    input.user.tier == "free"
    models := ["gpt-3.5-turbo", "local"]
}

allowed_models_for_user := models if {
    input.user.role == "user"
    input.user.tier == "premium"
    models := ["gpt-3.5-turbo", "claude-3-sonnet", "local"]
}

allowed_models_for_user := models if {
    input.user.role == "user"
    input.user.tier == "enterprise"
    models := [
        "gpt-3.5-turbo",
        "gpt-4",
        "claude-3-sonnet",
        "claude-3-opus",
        "local"
    ]
}

# Calculate allowed actions for user
allowed_actions_for_user := actions if {
    input.user.role == "admin"
    actions := ["chat", "admin", "manage_users", "view_logs"]
}

allowed_actions_for_user := actions if {
    input.user.role == "user"
    actions := ["chat"]
}

# Calculate rate limits for user tier
rate_limits_for_user := limits if {
    input.user.tier == "free"
    limits := {
        "requests_per_minute": 10,
        "tokens_per_month": 100000
    }
}

rate_limits_for_user := limits if {
    input.user.tier == "premium"
    limits := {
        "requests_per_minute": 100,
        "tokens_per_month": 1000000
    }
}

rate_limits_for_user := limits if {
    input.user.tier == "enterprise"
    limits := {
        "requests_per_minute": 1000,
        "tokens_per_month": "unlimited"
    }
}
