# ─── ECS Task Definition ─────────────────────────────────────────

resource "aws_ecs_task_definition" "backend" {
  family                   = "ai-multi-agent-backend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "backend"
      image     = "${aws_ecr_repository.backend.repository_url}:latest"
      essential = true
      portMappings = [
        { containerPort = 8400, protocol = "tcp" }
      ]
      environment = [
        { name = "CLOUD_PROVIDER", value = "aws" },
        { name = "AWS_REGION", value = var.aws_region },
        { name = "LOG_LEVEL", value = "INFO" },
        { name = "REDIS_URL", value = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:6379/0" },
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.backend.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8400/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])
}

# ─── ECS Service ────────────────────────────────────────────────

resource "aws_ecs_service" "backend" {
  name            = "ai-multi-agent-backend"
  cluster         = var.ecs_cluster_name
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.backend.id]
    assign_public_ip = false
  }
}
