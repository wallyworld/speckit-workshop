# Pet Store Requirements

Authoritative product requirements for the Pet Store application.
Phase 1 specifies the storage and HTTP API backend. Phase 2 specifies the
browser web user interface.

## Requirements

### Pet Catalog Backend (Phase 1)

- **CAT-1**: The service MUST allow adding a pet with a name and a
  non-negative initial stock count.
- **CAT-2**: The service MUST list pets and derive each pet's availability
  status strictly from whether its stock count is greater than zero.
- **CAT-3**: The service MUST retrieve an individual pet by its unique
  identifier and return a 404 error if not found.
- **CAT-4**: The service MUST allow deleting a pet by its unique identifier.

### Ordering and Inventory Backend (Phase 1)

- **ORD-1**: Placing an order for an unavailable pet (stock count zero or
  less) MUST fail with an error response.
- **ORD-2**: A successful order MUST decrease the pet's available stock
  count by exactly one.
- **ORD-3**: An order MUST NOT allow pet stock count to drop below zero
  under any sequential or concurrent condition.
- **ORD-4**: Canceling an open order MUST restore the pet's available
  stock count by exactly one.

### Pet Store Web UI (Phase 2)

- **UI-1**: The web UI MUST render the pet catalog showing name, current
  stock count, and a distinct visual badge for availability status.
- **UI-2**: The web UI MUST provide a pet creation form with client-side
  validation and refresh the catalog display immediately upon success.
- **UI-3**: The web UI MUST provide an order action for each catalog item
  that is visually disabled whenever stock count is zero.
- **UI-4**: The web UI MUST display active orders and provide a cancel
  action that updates both the order list and the catalog stock count in place.
- **UI-5**: The web UI MUST be served directly by the FastAPI backend as a
  static single-page application without requiring an external frontend build
  pipeline or node runtime.
- **UI-6**: The web UI MUST call the API with same-origin relative paths
  such as `/api/v1/pets`, and MUST NOT hardcode a host or port, so the UI
  works on any host or port that serves it.

