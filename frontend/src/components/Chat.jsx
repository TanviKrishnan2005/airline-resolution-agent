import ResolutionSteps from "./ResolutionSteps";
export default function Chat({
  customer,
  messages,
  input,
  setInput,
  sendMessage,
  loading,
  steps,
}) {
  function handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  }

  return (
    <section className="card conversationCard">

      <div className="conversationHeader">

        <div>
          <div className="sectionLabel">
            RESOLUTION DESK
          </div>

          <h2>{customer.name}'s case</h2>

          <div className="caseMeta">
            {customer.flight}
            <span>·</span>
            {customer.pnr}
          </div>
        </div>

        <div className="policyBadge">
          ✦ Policy-aware
        </div>

      </div>


      <div className="chatArea">

        {messages.length === 0 ? (

          <div className="emptyConversation">

            <div className="planeBubble">
              ✈
            </div>

            <h2>What's going on?</h2>

            <p>
              Tell me what happened and I'll figure
              out the next step.
            </p>

            <button
              className="scenarioButton"
              onClick={() =>
                setInput(
                  customer.statusType === "cancelled"
                    ? "I want a refund"
                    : "What help can I get for this delay?"
                )
              }
            >
              Try the scenario →
            </button>

          </div>

        ) : (

          <div className="messages">

            {messages.map((message, index) => (
              <div
                key={index}
                className={
                  message.role === "user"
                    ? "messageRow user"
                    : "messageRow agent"
                }
              >

                {message.role === "agent" && (
                  <div className="agentAvatar">
                    ✦
                  </div>
                )}

                <div
                  className={
                    message.role === "user"
                      ? "messageBubble userBubble"
                      : "messageBubble agentBubble"
                  }
                >
                  {message.text}
                </div>

              </div>
            ))}

            {loading && (
              <div className="messageRow agent">

                <div className="agentAvatar">
                  ✦
                </div>

                <div className="messageBubble agentBubble typing">
                  <span />
                  <span />
                  <span />
                </div>

              </div>
            )}

          </div>

        )}

      </div>


      <ResolutionSteps steps={steps} />


      <div className="inputWrapper">

        <textarea
          value={input}
          onChange={(event) =>
            setInput(event.target.value)
          }
          onKeyDown={handleKeyDown}
          placeholder="Tell the agent what you need..."
          rows={2}
        />

        <button
          className="sendButton"
          onClick={sendMessage}
          disabled={loading || !input.trim()}
        >
          Send <span>↗</span>
        </button>

      </div>

      <div className="inputHint">
        Enter to send · Shift + Enter for a new line
      </div>

    </section>
  );
}