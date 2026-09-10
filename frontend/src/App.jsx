import { useState } from "react";

import Predictions from "./pages/Predictions";
import RuleBuilder from "./pages/RuleBuilder";
import VehicleDetail from "./pages/VehicleDetail";
import AgentChat from "./pages/AgentChat";

import "./App.css";

function App() {
  const [page, setPage] = useState("predictions");

  const [selectedVehicle, setSelectedVehicle] =
    useState(null);

  const openVehicle = (vin, partCode) => {
    setSelectedVehicle({
      vin,
      partCode,
    });

    setPage("vehicle");
  };

return (
  <div className="app">

    <header className="header">
      <h2>FleetGuard AI</h2>
    </header>

    <nav className="nav">

      <button
        onClick={() =>
          setPage("predictions")
        }
      >
        Failure Probability
      </button>

      <button
        onClick={() =>
          setPage("rules")
        }
      >
        Rule Builder
      </button>

    </nav>

    <div className="layout">

      <section className="content">

        {page === "predictions" && (
          <Predictions
            onSelectVehicle={
              openVehicle
            }
          />
        )}

        {page === "rules" && (
          <RuleBuilder />
        )}

        {page === "vehicle" &&
          selectedVehicle && (
            <VehicleDetail
              vin={
                selectedVehicle.vin
              }
              partCode={
                selectedVehicle.partCode
              }
              onBack={() =>
                setPage("predictions")
              }
            />
          )}

      </section>

      <aside className="agent-panel">
        <AgentChat />
      </aside>

    </div>

  </div>
);
}

export default App;