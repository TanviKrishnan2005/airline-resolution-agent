export default function ActionRecord({
  actions,
  customer,
}) {
  const latestActions = actions.slice(-6).reverse();

  const resolvedActions = actions.filter(
    (action) =>
      !String(action.action || "")
        .toLowerCase()
        .includes("escal")
  );

  const escalatedActions = actions.filter((action) =>
    String(action.action || "")
      .toLowerCase()
      .includes("escal")
  );

  return (
    <>
      <div className="card actionCard">

        <div className="rightTitle">

          <div>
            <div className="sectionLabel">
              CASE ACTIVITY
            </div>

            <h2>Action record</h2>
          </div>

          <span className="liveDot" />

        </div>


        {latestActions.length === 0 ? (

          <div className="emptyActions">

            <div className="emptyActionIcon">
              ○
            </div>

            <strong>Nothing yet</strong>

            <p>
              Actions will appear here as the
              agent resolves the case.
            </p>

          </div>

        ) : (

          <div className="actionList">

            {latestActions.map((action, index) => {

              const escalated =
                String(action.action || "")
                  .toLowerCase()
                  .includes("escal");

              return (
                <div
                  key={index}
                  className={
                    escalated
                      ? "actionItem escalated"
                      : "actionItem"
                  }
                >

                  <div className="actionIcon">
                    {escalated ? "↗" : "✓"}
                  </div>

                  <div>
                    <strong>{action.action}</strong>

                    <span>
                      {action.pnr || customer.pnr}
                    </span>
                  </div>

                </div>
              );
            })}

          </div>

        )}

      </div>


      <div className="card statusCard">

        <div className="sectionLabel">
          CASE STATUS
        </div>

        {actions.length === 0 ? (

          <>
            <div className="statusText">
              Open
            </div>

            <p>
              Waiting for the customer's request.
            </p>
          </>

        ) : (

          <>
            {resolvedActions.length > 0 && (
              <div className="statusGroup resolved">
                <strong>✓ Resolved</strong>

                {resolvedActions.map((action, index) => (
                  <span key={index}>
                    {action.action}
                  </span>
                ))}
              </div>
            )}

            {escalatedActions.length > 0 && (
              <div className="statusGroup escalatedGroup">
                <strong>↗ Human review</strong>

                {escalatedActions.map((action, index) => (
                  <span key={index}>
                    {action.action}
                  </span>
                ))}
              </div>
            )}
          </>

        )}

      </div>


      <div className="authorityCard">

        <div className="authorityIcon">
          !
        </div>

        <div>
          <strong>Agent boundaries</strong>

          <p>
            Requests outside policy are routed
            to a human instead of being guessed
            or overridden.
          </p>
        </div>

      </div>
    </>
  );
}