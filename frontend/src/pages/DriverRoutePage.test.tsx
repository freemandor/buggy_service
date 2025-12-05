import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, act } from "@testing-library/react";
import DriverRoutePage from "./DriverRoutePage";
import type { DriverRouteStop } from "../api/driver";

vi.mock("../components/Layout", () => ({
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock("../api/driver", () => {
  return {
    fetchDriverRoute: vi.fn(),
    driverStartStop: vi.fn(),
    driverCompleteStop: vi.fn(),
  };
});

const mockFetch = vi.mocked(require("../api/driver").fetchDriverRoute);

type Deferred<T> = {
  promise: Promise<T>;
  resolve: (value: T) => void;
};

const deferred = <T,>(): Deferred<T> => {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((res) => {
    resolve = res;
  });
  return { promise, resolve };
};

const makeStop = (id: number, status: DriverRouteStop["status"]) => ({
  id,
  stop_type: "PICKUP",
  status,
  poi: { id: 1, name: "Test POI", code: "TP" },
  ride_request_code: "RIDE",
  num_guests: 2,
  sequence_index: id,
});

describe("DriverRoutePage polling", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    mockFetch.mockReset();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("keeps latest polling result when earlier request resolves late", async () => {
    const first = deferred<DriverRouteStop[]>();
    const second = deferred<DriverRouteStop[]>();

    mockFetch.mockImplementationOnce(() => first.promise);
    mockFetch.mockImplementationOnce(() => second.promise);

    render(<DriverRoutePage />);

    // Trigger second poll
    await act(async () => {
      vi.advanceTimersByTime(3000);
    });

    await act(async () => {
      second.resolve([makeStop(2, "ON_ROUTE")]);
      await second.promise;
    });

    expect(await screen.findByText(/ON_ROUTE/)).toBeInTheDocument();

    // Now resolve the first (older) request; UI should stay on ON_ROUTE.
    await act(async () => {
      first.resolve([makeStop(1, "PLANNED")]);
      await first.promise;
    });

    expect(screen.getByText(/ON_ROUTE/)).toBeInTheDocument();
    expect(screen.queryByText(/PLANNED/)).not.toBeNull();
  });
});
