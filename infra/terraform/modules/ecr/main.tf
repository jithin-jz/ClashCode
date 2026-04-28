resource "aws_ecr_repository" "core" {
  name                 = "${var.project_name}-core"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "chat" {
  name                 = "${var.project_name}-chat"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "ai" {
  name                 = "${var.project_name}-ai"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "analytics" {
  name                 = "${var.project_name}-analytics"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

# Lifecycle policy to keep only last 10 images to save costs
resource "aws_ecr_lifecycle_policy" "cleanup" {
  for_each = toset([
    aws_ecr_repository.core.name,
    aws_ecr_repository.chat.name,
    aws_ecr_repository.ai.name,
    aws_ecr_repository.analytics.name
  ])

  repository = each.value

  policy = <<EOF
{
    "rules": [
        {
            "rulePriority": 1,
            "description": "Keep last 10 images",
            "selection": {
                "tagStatus": "any",
                "countType": "imageCountMoreThan",
                "countNumber": 10
            },
            "action": {
                "type": "expire"
            }
        }
    ]
}
EOF
}
