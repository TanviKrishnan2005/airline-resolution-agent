import { useEffect, useState } from "react";

import PassengerCard from "./components/PassengerCard";
import FlightCard from "./components/FlightCard";
import Chat from "./components/Chat";
import ActionRecord from "./components/ActionRecord";

import "./styles.css";

const API_URL = "http://127.0.0.1:8000";

export default function App() {
  const [customers, setCustomers] = useState([]);
  const [bookings, setBookings] = useState([]);

  const [customer, setCustomer] = useState(null);

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");

  const [actions, setActions] = useState([]);

  const [loading, setLoading] = useState(false);
  const [dataLoading, setDataLoading] = useState(true);

  // =========================================================
  // INITIAL LOAD
  // =========================================================

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const [customersRes, bookingsRes] =
        await Promise.all([
          fetch(`${API_URL}/customers`),
          fetch(`${API_URL}/bookings`),
        ]);

      const customersData =
        await customersRes.json();

      const bookingsData =
        await bookingsRes.json();

      setCustomers(customersData);
      setBookings(bookingsData);

      if (customersData.length > 0) {
        const firstCustomer =
          customersData[0];

        setCustomer(firstCustomer);

        await loadActions(
          firstCustomer.booking_reference
        );
      }
    } catch (error) {
      console.error(
        "Failed to load data:",
        error
      );
    } finally {
      setDataLoading(false);
    }
  }

  // =========================================================
  // LOAD ACTIONS FROM BACKEND
  // =========================================================

  async function loadActions(pnr) {
    try {
      const response =
        await fetch(`${API_URL}/actions`);

      if (!response.ok) {
        throw new Error(
          `HTTP ${response.status}`
        );
      }

      const data =
        await response.json();

      const allActions =
        Array.isArray(data)
          ? data
          : data.actions || [];

      const customerActions =
        allActions.filter(
          (action) =>
            action.pnr === pnr
        );

      setActions(
        removeDuplicateActions(
          customerActions
        )
      );
    } catch (error) {
      console.error(
        "Failed to load actions:",
        error
      );
    }
  }

  // =========================================================
  // REMOVE DUPLICATES
  // =========================================================

  function removeDuplicateActions(
    actionList
  ) {
    const seen = new Set();

    return actionList.filter(
      (action) => {
        const key =
          `${action.pnr}|${action.action}|${action.details}`;

        if (seen.has(key)) {
          return false;
        }

        seen.add(key);

        return true;
      }
    );
  }

  // =========================================================
  // BOOKING LOOKUP
  // =========================================================

  function getPrimaryBooking(
    customerData,
    bookingsData = bookings
  ) {
    if (!customerData) {
      return null;
    }

    const customerBookings =
      bookingsData.filter(
        (booking) =>
          booking.pnr ===
          customerData.booking_reference
      );

    const disruptedBooking =
      customerBookings.find(
        (booking) =>
          booking.status === "Cancelled" ||
          booking.status === "Delayed"
      );

    return (
      disruptedBooking ||
      customerBookings[0] ||
      null
    );
  }

  // =========================================================
  // CUSTOMER VIEW
  // =========================================================

  function getCustomerView(
    customerData,
    bookingsData = bookings
  ) {
    const booking =
      getPrimaryBooking(
        customerData,
        bookingsData
      );

    if (
      !customerData ||
      !booking
    ) {
      return null;
    }

    let from = "";
    let to = "";

    if (booking.route) {
      const parts =
        booking.route.split("→");

      from =
        parts[0]?.trim() || "";

      to =
        parts[1]?.trim() || "";
    }

    return {
      name: customerData.name,

      tier:
        customerData.loyalty_tier,

      pnr:
        customerData.booking_reference,

      flight:
        booking.flight || "—",

      route:
        booking.route || "—",

      from,
      to,

      date:
        booking.date,

      departure:
        booking.scheduled_departure,

      newDeparture:
        booking.new_departure,

      status:
        booking.status,

      statusType:
        booking.status === "Cancelled"
          ? "cancelled"
          : booking.status === "Delayed"
            ? "delayed"
            : "normal",

      delayHours:
        booking.delay_hours || 0,
    };
  }

  // =========================================================
  // SELECT CUSTOMER
  // =========================================================

  async function selectCustomer(
    selectedCustomer,
    bookingsData = bookings
  ) {
    setCustomer(
      selectedCustomer
    );

    // Reset conversation
    setMessages([]);
    setInput("");

    // Load this customer's existing actions
    await loadActions(
      selectedCustomer.booking_reference
    );
  }

  // =========================================================
  // SEND MESSAGE
  // =========================================================

  async function sendMessage() {
    const text =
      input.trim();

    if (
      !text ||
      !customer ||
      loading
    ) {
      return;
    }

    // Show user message immediately
    setMessages(
      (previous) => [
        ...previous,
        {
          role: "user",
          text,
        },
      ]
    );

    setInput("");
    setLoading(true);

    try {
      const response =
        await fetch(
          `${API_URL}/chat`,
          {
            method: "POST",

            headers: {
              "Content-Type":
                "application/json",
            },

            body: JSON.stringify({
              customer:
                customer.name,

              message: text,
            }),
          }
        );

      if (!response.ok) {
        throw new Error(
          `HTTP ${response.status}`
        );
      }

      const data =
        await response.json();

      // -----------------------------------------------------
      // AGENT RESPONSE
      // -----------------------------------------------------

      setMessages(
        (previous) => [
          ...previous,
          {
            role: "agent",
            text:
              data.response ||
              "I couldn't process that request.",
          },
        ]
      );

      // -----------------------------------------------------
      // IMPORTANT FIX
      //
      // Always reload backend action log.
      // Do NOT depend only on data.actions.
      // -----------------------------------------------------

      await loadActions(
        customer.booking_reference
      );

    } catch (error) {
      console.error(
        "Chat error:",
        error
      );

      setMessages(
        (previous) => [
          ...previous,
          {
            role: "agent",
            text:
              "I'm sorry, something went wrong while processing your request.",
          },
        ]
      );
    } finally {
      setLoading(false);
    }
  }

  // =========================================================
  // RESOLUTION STEPS
  // =========================================================

  function getResolutionSteps() {
    if (!customer) {
      return [];
    }

    const booking =
      getPrimaryBooking(customer);

    if (!booking) {
      return [
        {
          type: "waiting",
          text:
            "Waiting for booking",
        },
      ];
    }

    const hasMessages =
      messages.length > 0;

    const hasEscalation =
      actions.some(
        (action) =>
          String(
            action.action || ""
          )
            .toLowerCase()
            .includes("escal")
      );

    const hasResolution =
      actions.some(
        (action) =>
          !String(
            action.action || ""
          )
            .toLowerCase()
            .includes("escal")
      );

    const steps = [
      {
        type: "done",
        text:
          "Customer identified",
      },

      {
        type: "done",
        text:
          `Booking ${customer.booking_reference} verified`,
      },
    ];

    if (!hasMessages) {
      steps.push({
        type: "waiting",
        text:
          "Waiting for request",
      });

      return steps;
    }

    steps.push({
      type: "done",
      text:
        "Request understood",
    });

    if (hasEscalation) {
      steps.push({
        type: "warning",
        text:
          "Human review required",
      });
    } else if (hasResolution) {
      steps.push({
        type: "done",
        text:
          "Policy action completed",
      });
    } else {
      steps.push({
        type: "waiting",
        text:
          "Processing request",
      });
    }

    return steps;
  }

  // =========================================================
  // POLICY SNAPSHOT
  // =========================================================

  function getPolicySnapshot() {
    const booking =
      getPrimaryBooking(customer);

    if (!booking || !customer) {
      return [];
    }

    if (
      booking.status ===
      "Cancelled"
    ) {
      return [
        "Airline-caused cancellation",
        "Free rebooking within 24h",
        "OR full refund",
        "Refund to original payment method",
        "Refund within 7 business days",
        `${customer.loyalty_tier} → priority rebooking`,
      ];
    }

    if (
      booking.status ===
      "Delayed"
    ) {
      const delay =
        booking.delay_hours || 0;

      const policy = [];

      if (delay >= 3) {
        policy.push(
          "Meal voucher"
        );

        policy.push(
          "Lounge access"
        );
      }

      if (delay > 5) {
        policy.push(
          "Hotel for delayed hours only"
        );
      }

      policy.push(
        `${customer.loyalty_tier} → priority rebooking`
      );

      return policy;
    }

    return [
      "Check booking",
      "Apply airline policy",
      "Execute permitted actions",
      "Escalate restricted requests",
    ];
  }

  // =========================================================
  // LOADING
  // =========================================================

  if (dataLoading) {
    return (
      <div className="loadingScreen">

        <div className="planeBubble">
          ✈
        </div>

        <strong>
          Loading resolution desk...
        </strong>

      </div>
    );
  }

  // =========================================================
  // CUSTOMER VIEW
  // =========================================================

  const customerView =
    getCustomerView(customer);

  if (!customerView) {
    return (
      <div className="loadingScreen">

        <strong>
          No customer data available.
        </strong>

      </div>
    );
  }

  const resolutionSteps =
    getResolutionSteps();

  const policySnapshot =
    getPolicySnapshot();

  // =========================================================
  // UI
  // =========================================================

  return (
    <div className="app">

      {/* HEADER */}

      <header className="topbar">

        <div className="brand">

          <div className="brandIcon">
            ✈
          </div>

          <div>

            <div className="brandName">
              SkyResolve
            </div>

            <div className="brandSub">
              AionOS · Customer Resolution Agent
            </div>

          </div>

        </div>

        <div className="onlineStatus">
          <span className="onlineDot" />
          Agent online
        </div>

      </header>

      {/* DEMO HEADER */}

      <section className="demoHeader">

        <div>

          <div className="eyebrow">
            AIRLINE DISRUPTION DESK
          </div>

          <h1>
            Resolve the issue.
            <span>
              {" "}Respect the policy.
            </span>
          </h1>

          <p>
            Customer-facing resolution
            agent for disrupted journeys.
          </p>

        </div>

        {/* CUSTOMER SWITCHER */}

        <div className="customerTabs">

          {customers.map(
            (item) => {

              const initials =
                item.name
                  .split(" ")
                  .map(
                    (word) =>
                      word[0]
                  )
                  .join("");

              const active =
                customer?.booking_reference ===
                item.booking_reference;

              return (
                <button
                  key={
                    item.booking_reference
                  }

                  className={
                    active
                      ? "customerTab active"
                      : "customerTab"
                  }

                  onClick={() =>
                    selectCustomer(item)
                  }
                >

                  <span className="tabAvatar">
                    {initials}
                  </span>

                  {
                    item.name.split(" ")[0]
                  }

                </button>
              );
            }
          )}

        </div>

      </section>

      {/* MAIN */}

      <main className="layout">

        {/* LEFT */}

        <aside className="leftColumn">

          <PassengerCard
            customer={
              customerView
            }
          />

          <FlightCard
            customer={
              customerView
            }
          />

          <div className="card capabilitiesCard">

            <div className="sectionLabel">
              AGENT CAN
            </div>

            <div className="capability">
              <span>✓</span>
              Check booking
            </div>

            <div className="capability">
              <span>✓</span>
              Apply airline policy
            </div>

            <div className="capability">
              <span>✓</span>
              Execute permitted actions
            </div>

            <div className="capability">
              <span>✓</span>
              Escalate restricted requests
            </div>

          </div>

          <div className="card policyCard">

            <div className="sectionLabel">
              POLICY SNAPSHOT
            </div>

            {policySnapshot.map(
              (policy, index) => (
                <div
                  className="policyLine"
                  key={index}
                >
                  <span>→</span>
                  {policy}
                </div>
              )
            )}

          </div>

        </aside>

        {/* CHAT */}

        <Chat
          customer={
            customerView
          }

          messages={
            messages
          }

          input={
            input
          }

          setInput={
            setInput
          }

          sendMessage={
            sendMessage
          }

          loading={
            loading
          }

          steps={
            resolutionSteps
          }
        />

        {/* RIGHT */}

        <aside className="rightColumn">

          <ActionRecord
            actions={
              actions
            }

            customer={
              customerView
            }
          />

        </aside>

      </main>

    </div>
  );
}