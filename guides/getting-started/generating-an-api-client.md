<p align="center"><img src="../../resources/images/Serviceware-horizon-logo-rgb.svg" alt="Serviceware" width="350"></p>

# Generating an API Client

The Serviceware Knowledge REST API is described by an [OpenAPI](https://www.openapis.org/) specification. Code-generation tools can read this specification and produce a fully typed client library in the language of your choice, saving you from writing boilerplate HTTP and serialization code by hand. The generated client gives you typed method signatures, request/response models, and compile-time safety for every API operation.

## Obtaining the OpenAPI Specification

Download the specification from your Knowledge instance:

```
https://<your-instance>/sabio-web/services/api-docs
```

The endpoint returns the specification as a YAML document. Save it to a local file for use with the code generator:

```bash
curl -o knowledge-api.yaml https://<your-instance>/sabio-web/services/api-docs
```

## Generating a Client

[Swagger Codegen](https://github.com/swagger-api/swagger-codegen) is the recommended tool for generating client libraries from the OpenAPI specification.

### Java

```bash
swagger-codegen-cli generate -i knowledge-api.yaml -l java -o ./generated-client
```

This produces a Maven project under `./generated-client` containing model classes, API interfaces, and a pre-configured HTTP client.

### Python

```bash
swagger-codegen-cli generate -i knowledge-api.yaml -l python -o ./generated-client
```

This produces a Python package under `./generated-client` with typed models and API client classes.

### Other Languages

Swagger Codegen supports many additional languages and frameworks, including C#, TypeScript, Go, Ruby, and more. Refer to the [Swagger Codegen documentation](https://github.com/swagger-api/swagger-codegen#overview) for the full list of supported targets and configuration options.

## Authentication

The generated client handles request and response serialization, but it does **not** configure authentication headers automatically. You must set up authentication separately before making API calls.

> **Note:** Refer to the [Authentication](../getting-started/authentication.md) guide for details on how to authenticate your requests using session tokens, API keys, or OAuth2 bearer tokens.

## Next Steps

- [Authentication](../getting-started/authentication.md) -- Learn how to authenticate API requests against your Knowledge instance.
