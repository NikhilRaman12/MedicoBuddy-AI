export class APIError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public responseBody?: unknown
  ) {
    super(message);
    this.name = "APIError";
  }
}

export class TimeoutError extends Error {
  constructor(message = "Request timed out") {
    super(message);
    this.name = "TimeoutError";
  }
}

export class SchemaValidationError extends Error {
  constructor(message: string, public errors: unknown) {
    super(message);
    this.name = "SchemaValidationError";
  }
}
