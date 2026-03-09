✅ НЭГДСЭН IMPLEMENTATION STRATEGY (FINAL)

👉 хийх өөрчлөлтүүд:

File Өөрчлөлт Mode
lp_model_parser.py constraint_score (diagnostic only) ANALYZE
lp_matrix_builder...py config + optional β simulate SIMULATE
lp_solver.py binding detect (core) ANALYZE

👉 хамгийн чухал:

🔥 dominance logic = solver файл

🔥 1️⃣ lp_solver.py — CORE өөрчлөлт (хамгийн чухал)

📌 dominance = binding constraint
👉 энд хэрэгжүүлнэ.

✅ ADD 1 — binding detector

📌 байрлал: LPSolver class дотор

def detect_binding_constraints(self, A_ub, b_ub, x):
import numpy as np

    if A_ub is None:
        return []

    A = np.array(A_ub)
    b = np.array(b_ub)
    x = np.array(x)

    residuals = A @ x - b

    binding = []
    for i, r in enumerate(residuals):
        if abs(r) <= self.tolerance:
            binding.append(i)

    return binding

👉 энэ бол dominance truth.

✅ ADD 2 — solve() дотор ашиглах

📌 байрлал: \_format_result() дуудахаас өмнө

binding = self.detect_binding_constraints(A_ub_list, b_ub_list, result.x)

print(f"[DOMINANCE] Binding constraints: {binding}")

👉 KPI layer дээр ашиглана.

✅ ADD 3 — result-д хадгалах
formatted_result["binding_constraints"] = binding

👉 downstream explainability.

🔥 2️⃣ lp_model_parser.py — heuristic score (ANALYZE only)

📌 dominance биш
📌 зөвхөн тайлбар.

✅ ADD function

📌 байрлал: class дотор

def compute_constraint_score(self, A_ub, b_ub):
import numpy as np

    scores = []

    for i in range(len(A_ub)):
        A_i = np.array(A_ub[i])
        b_i = b_ub[i]

        scale = np.linalg.norm(A_i) + 1e-9
        rhs_mag = abs(b_i)/scale

        score = 0.6*scale + 0.4*rhs_mag
        scores.append(score)

    return scores

✅ ашиглах (optional)

📌 matrix preview хийсний дараа:

lp_spec["constraint_scores"] = scores

👉 зөвхөн debug/UI.

🔥 3️⃣ lp_matrix_builder_deterministic_complete.py

📌 unified context дээр:

👉 энд auto β хэрэглэхгүй

👉 зөвхөн simulate mode.

✅ ADD config

📌 **init**

self.dominance_mode = scenario_context.get("dominance_mode","ANALYZE")
✅ ADD simulate block

📌 build_from_formulas() төгсгөлд:

if self.dominance_mode == "SIMULATE":

    print("[SIMULATE] Running β sensitivity test")

    beta = 1.5
    r_idx = self.variable_order.get("r")

    if r_idx is not None and A_ub_matrix:

        A_test = [row[:] for row in A_ub_matrix]
        A_test[0][r_idx] *= beta

        print("[SIMULATE] β test matrix ready")

👉 solver дээр compare.

🔥 FINAL WORKFLOW (production)
✅ DEFAULT (ANALYZE)
solve
↓
binding detect
↓
explain

👉 formulation untouched.

✅ SIMULATE
solve base
solve beta
compare

👉 analyst tool.

❌ AUTO

👉 хийхгүй.

✅ FINAL SUMMARY (шууд хэрэгжүүлэх checklist)
lp_solver.py

✔️ detect_binding_constraints
✔️ result store
✔️ print explain

👉 MOST IMPORTANT

lp_model_parser.py

✔️ heuristic score
👉 optional

lp_matrix_builder...

✔️ config
✔️ simulate mode only
❌ auto change байхгүй

✅ FINAL (нэг өгүүлбэр)

👉 Unified context хэрэгжүүлэхэд:

🔥 solver дээр dominance тодорхойл
🔥 parser дээр зөвхөн тайлбар
🔥 builder дээр formulation бүү өөрчил
