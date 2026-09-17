export default function ResolutionSteps({ steps }) {
  return (
    <div className="resolutionSteps">

      <div className="resolutionTitle">
        <span>✦</span>
        Resolution steps
      </div>

      <div className="steps">

        {steps.map((step, index) => (
          <div
            key={index}
            className={`step ${step.type}`}
          >
            <span>
              {step.type === "warning"
                ? "!"
                : step.type === "waiting"
                ? "○"
                : "✓"}
            </span>

            {step.text}
          </div>
        ))}

      </div>

    </div>
  );
}