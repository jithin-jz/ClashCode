resource "aws_dynamodb_table" "chat_messages" {
  name           = "${var.project_name}-${var.environment}-chat-messages"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "room_id"
  range_key      = "timestamp"

  attribute {
    name = "room_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "N"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-chat-table"
    Environment = var.environment
  }
}

output "table_name" {
  value = aws_dynamodb_table.chat_messages.name
}

output "table_arn" {
  value = aws_dynamodb_table.chat_messages.arn
}
