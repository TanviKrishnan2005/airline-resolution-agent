export default function FlightCard({ customer }) {
  return (
    <div className="card flightCard">

      <div className="flightTop">
        <div>
          <div className="sectionLabel">YOUR FLIGHT</div>

          <div className="flightNumber">
            {customer.flight}
          </div>
        </div>

        <span
          className={
            customer.statusType === "cancelled"
              ? "flightStatus cancelled"
              : "flightStatus delayed"
          }
        >
          {customer.status}
        </span>
      </div>

      <div className="route">

        <div>
          <strong>{customer.from}</strong>
          <span>{customer.departure}</span>
        </div>

        <div className="flightPath">
          <div />
          <span>✈</span>
          <div />
        </div>

        <div className="destination">
          <strong>{customer.to}</strong>
          <span>{customer.newDeparture || "—"}</span>
        </div>

      </div>

      <div className="flightDate">
        <span>▣</span>
        {customer.date}
      </div>

    </div>
  );
}