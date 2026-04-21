# ─── CloudWatch ─────────────────────────────────────────────────

resource "aws_cloudwatch_log_group" "backend" {
  name              = "/ecs/ai-multi-agent-backend"
  retention_in_days = 7
}
