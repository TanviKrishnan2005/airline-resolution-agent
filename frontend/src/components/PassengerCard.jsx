export default function PassengerCard({ customer }) {
  const initials = customer.name
    .split(" ")
    .map((word) => word[0])
    .join("");

  return (
    <div className="card passengerCard">
      <div className="sectionLabel">PASSENGER</div>

      <div className="passengerInfo">
        <div className="bigAvatar">{initials}</div>

        <div>
          <h2>{customer.name}</h2>

          <span className="tier">
            {customer.tier} member
          </span>
        </div>
      </div>

      <div className="pnr">
        <span>Booking reference</span>
        <strong>{customer.pnr}</strong>
      </div>
    </div>
  );
}