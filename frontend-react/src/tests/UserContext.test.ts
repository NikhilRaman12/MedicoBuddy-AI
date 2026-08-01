import { describe, it, expect } from "vitest";
import { useStore } from "../state/useStore";

describe("UserContext Enum Contract", () => {
  it("never interprets unknown or not_pregnant as pregnant", () => {
    const store = useStore.getState();

    // Default pregnancy_status must be 'unknown'
    expect(store.userContext.pregnancy_status).toBe("unknown");

    // Setting not_pregnant
    store.setUserContext({ pregnancy_status: "not_pregnant" });
    expect(useStore.getState().userContext.pregnancy_status).toBe("not_pregnant");

    // Must be distinct from 'pregnant'
    expect(useStore.getState().userContext.pregnancy_status).not.toBe("pregnant");
  });
});
