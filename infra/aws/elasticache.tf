# ─── ElastiCache Redis ──────────────────────────────────────────

resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "multi-agent-redis"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
  security_group_ids   = [aws_security_group.redis.id]
  subnet_group_name    = aws_elasticache_subnet_group.redis.name
}

resource "aws_elasticache_subnet_group" "redis" {
  name       = "multi-agent-redis"
  subnet_ids = var.private_subnet_ids
}
