File Юу хийх вэ Яагаад
lp_model_parser.py dominance prediction solve өмнө
lp_matrix_builder...py constraint_score compute + β apply formulation control
lp_solver.py post-solve validate/report final dominance confirm

👉 доор тус бүрээр нь код өгнө.

🔥 1️⃣ lp_model_parser.py — dominance prediction нэмэх

📌 байрлал: LPModelParser class дотор шинэ function.

👉 зорилго: solve өмнө dominance estimate

✅ ADD: function
def predict_constraint_dominance(self, A_ub, b_ub, xmin=None, xmax=None):
"""
Predict dominant constraint before solve.
"""
import numpy as np

    scores = []

    # center estimate
    if xmin is not None and xmax is not None:
        x_center = (np.array(xmin) + np.array(xmax)) / 2
    else:
        x_center = np.zeros(A_ub.shape[1])

    for i in range(len(A_ub)):
        A_i = np.array(A_ub[i])
        b_i = b_ub[i]

        # scale
        scale = np.linalg.norm(A_i) + 1e-9

        # rhs magnitude
        rhs_mag = abs(b_i) / scale

        # slack approx
        slack = b_i - A_i @ x_center
        slack_term = 1.0 / (abs(slack) + 1e-6)

        score = 0.4*scale + 0.3*rhs_mag + 0.3*slack_term

        scores.append(score)

    return scores

✅ USE хийх газар

detect_lp_formulas() дараа:

lp_spec["dominance_scores"] = self.predict_constraint_dominance(
A_ub_preview, b_ub_preview, xmin, xmax
)

👉 (preview matrix build хийсний дараа дуудаж болно)

🔥 2️⃣ lp_matrix_builder_deterministic_complete.py — core logic

📌 энэ файл дээр dominance control хийх ёстой.

✅ STEP 1 — constraint_score compute

📌 байрлал: \_build_inequality_constraints() дараа.

add:

def \_compute_constraint_scores(self, A_ub, b_ub):
import numpy as np

    scores = []
    for i in range(len(A_ub)):
        A_i = np.array(A_ub[i])
        b_i = b_ub[i]

        scale = np.linalg.norm(A_i) + 1e-9
        rhs_mag = abs(b_i) / scale

        slack_guess = abs(b_i)  # fallback guess
        slack_term = 1/(slack_guess+1e-6)

        score = 0.4*scale + 0.3*rhs_mag + 0.3*slack_term
        scores.append(score)

    return scores

✅ STEP 2 — β auto-adjust apply

📌 байрлал: build_from_formulas() дотор matrix build дараа.

add:

scores = self.\_compute_constraint_scores(A_ub_matrix, b_ub_vector)

# assume first constraint = profit

profit_score = scores[0]
box_score = max(scores[1:])

if profit_score < box_score:
beta = min(5.0, max(1.0, 1.1\*box_score/profit_score))

    print(f"[AUTO β] Adjusting β to {beta}")

    # apply β → modify r coefficient
    r_idx = self.variable_order.get("r")
    if r_idx is not None:
        A_ub_matrix[0][r_idx] *= beta

👉 энэ хамгийн чухал 🔥

🔥 3️⃣ lp_solver.py — post-solve dominance confirm

📌 байрлал: solve() дараа.

✅ ADD:
def detect_binding_constraints(self, A_ub, b_ub, x):
import numpy as np

    residuals = np.array(A_ub) @ np.array(x) - np.array(b_ub)

    binding = []
    for i, r in enumerate(residuals):
        if abs(r) < self.tolerance:
            binding.append(i)

    return binding

✅ USE:

solve() return өмнө:

binding = self.detect_binding_constraints(A_ub_list, b_ub_list, result.x)

print(f"[DOMINANCE] Binding constraints: {binding}")

👉 production дээр KPI explanation болно.

🔥 FINAL FLOW (чиний system дээр)

1️⃣ Parser:

👉 dominance estimate

2️⃣ Matrix builder:

👉 β auto-adjust
👉 dominance shift

3️⃣ Solver:

👉 binding confirm
