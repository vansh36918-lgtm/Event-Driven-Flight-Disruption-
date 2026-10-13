# CURRENT_TASK.md — Active Sprint Focus

- **Current Goal**: Phase 18: Multi-Leg Crew Deadhead Recovery & CRS E-Hotel Voucher Integration.
- **Verification Status**:
  - Phase 17 completed: Monochromatic minimalist black-and-white theme & 3D Three.js interactive flight vector globe live on `http://localhost:8000`.
  - `python test_system.py`: 14/14 test suites passing.
  - Active background daemon `task-866` running `python run.py`.
  - Active 10-hour scheduler `task-669` waking agent continuously.
- **Next Steps**:
  - Implement `app/engine/hotel_engine.py` for automated CRS/Sabre electronic hotel & meal vouchers for overnight IRROPS delays (>6h or 22:00-06:00).
  - Implement Crew Deadhead Recovery in `app/engine/crew_engine.py` to re-position reserve crew members on non-disrupted flights to rescue downstream rotations.
  - Expose API endpoints in `app/main.py`.
  - Update `test_system.py` with test suite 15.







