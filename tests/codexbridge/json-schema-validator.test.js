/**
 * JsonSchemaValidator unit tests ensure schema loading and caching behave.
 */

import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { promises as fs } from "fs";
import os from "os";
import path from "path";

import JsonSchemaValidator, {
  SchemaValidationError,
} from "../../codexbridge/src/validation/json-schema-validator.js";

describe("JsonSchemaValidator", () => {
  it("validates payloads using in-memory schemas", async () => {
    const validator = new JsonSchemaValidator({
      schema: {
        type: "object",
        properties: {
          name: { type: "string" },
        },
        required: ["name"],
        additionalProperties: false,
      },
    });

    const success = await validator.validate({ name: "Codex" });
    assert.equal(success.valid, true);

    const failure = await validator.validate({});
    assert.equal(failure.valid, false);
    assert.ok(
      failure.errors?.some((issue) => issue.message?.includes("required"))
    );
  });

  it("throws SchemaValidationError when schema JSON is invalid", async () => {
    const tmpDir = await fs.mkdtemp(
      path.join(os.tmpdir(), "schema-validator-")
    );
    const schemaPath = path.join(tmpDir, "broken-schema.json");
    await fs.writeFile(schemaPath, "{invalid");

    const validator = new JsonSchemaValidator({ schemaPath });
    await assert.rejects(validator.validate({}), (error) => {
      assert.ok(error instanceof SchemaValidationError);
      assert.match(error.message, /Failed to parse schema/);
      return true;
    });

    await fs.rm(tmpDir, { recursive: true, force: true });
  });

  it("compiles schemas only once per instance", async () => {
    let compileCount = 0;
    const schema = { type: "object" };
    const stubValidator = (_payload) => {
      stubValidator.errors = [];
      return true;
    };
    const stubAjv = {
      compile(receivedSchema) {
        compileCount += 1;
        assert.deepEqual(receivedSchema, schema);
        return stubValidator;
      },
    };

    const validator = new JsonSchemaValidator({ schema, ajv: stubAjv });
    await validator.validate({});
    await validator.validate({ another: "payload" });
    assert.equal(compileCount, 1);
  });
});
