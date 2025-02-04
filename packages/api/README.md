# api/
- A Node.js service (Express, NestJS, or similar) that:
- Loads grid/obstacle data at startup.
- Exposes endpoints for pathfinding requests, e.g., POST /api/path with start, end.
- Uses pathfinding-core internally to compute routes.