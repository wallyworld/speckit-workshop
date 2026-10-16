# Pet Store Delivery Roadmap

| ID | Sub-feature | Intent | Scope boundary | Depends on | Status | Completes (RQ) | Advances (RQ) | Sub-spec |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R1 | Pet catalog API | Fast, minimal CRUD API for pets and inventory stock. | Storage and API only; no order processing. | - | done | CAT-1, CAT-2, CAT-3, CAT-4 | - | [`001-pet-catalog`](specs/001-pet-catalog/) |
| R2 | Order placement API | Safe order placement and cancellation with inventory guards. | Backend order endpoints; no frontend UI. | R1 | done | ORD-1, ORD-2, ORD-3, ORD-4 | - | [`002-order-placement`](specs/002-order-placement/) |
| R3 | Pet store Web UI | Interactive browser frontend connecting catalog and orders. | Client frontend served by FastAPI; uses existing R1/R2 API; no external frontend build tools. | R1, R2 | planned | UI-1, UI-2, UI-3, UI-4, UI-5 | - | [`003-web-ui`](specs/003-web-ui/) |

