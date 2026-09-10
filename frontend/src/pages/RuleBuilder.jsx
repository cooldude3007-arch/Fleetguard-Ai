import { useEffect, useState } from "react";
import api from "../services/api";

function RuleBuilder() {
  const [parts, setParts] = useState([]);
  const [selectedPart, setSelectedPart] = useState("");
  const [rules, setRules] = useState([]);

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    fetchParts();
  }, []);

  const fetchParts = async () => {
    try {
      const response = await api.get("/parts");

      setParts(response.data);

      if (response.data.length > 0) {
        setSelectedPart(
          response.data[0].part_code
        );
      }
    } catch (error) {
      console.error(error);

      setError(
        "Could not load parts."
      );
    }
  };

  useEffect(() => {
    if (selectedPart) {
      fetchRules();
    }
  }, [selectedPart]);

  const fetchRules = async () => {
    try {
      setLoading(true);
      setError("");
      setMessage("");

      const response = await api.get(
        `/rules/${selectedPart}`
      );

      setRules(
        response.data.signals
      );
    } catch (error) {
      console.error(error);

      setError(
        "Could not load rule."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = (signalName) => {
    setRules(
      rules.map((rule) =>
        rule.signal === signalName
          ? {
              ...rule,
              included:
                !rule.included,
            }
          : rule
      )
    );
  };

  const saveRule = async () => {
    try {
      setSaving(true);
      setError("");
      setMessage("");

      const payload = {
        signals: rules.map((rule) => ({
          signal: rule.signal,
          included: rule.included,
        })),
      };

      await api.put(
        `/rules/${selectedPart}`,
        payload
      );

      setMessage(
        "Rule saved successfully."
      );

      await fetchRules();
    } catch (error) {
      console.error(error);

      setError(
        "Could not save rule."
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <h1>Rule Builder</h1>

      <p>
         Configure the signals used to calculate
         failure probability.
      </p>

      <div>
        <label>
          Select Part:{" "}
        </label>

        <select
          value={selectedPart}
          onChange={(e) =>
            setSelectedPart(
              e.target.value
            )
          }
        >
          {parts.map((part) => (
            <option
              key={part.part_code}
              value={part.part_code}
            >
              {part.part_name}
            </option>
          ))}
        </select>
      </div>

      {loading && (
        <p>Loading rule...</p>
      )}

      {error && (
        <p>{error}</p>
      )}

      {message && (
        <p>{message}</p>
      )}

      {!loading && rules.length > 0 && (
        <>
          <table
            border="1"
            cellPadding="8"
          >
            <thead>
              <tr>
                <th>Signal</th>
                <th>ML Weight</th>
                <th>Included</th>
              </tr>
            </thead>

            <tbody>
              {rules.map((rule) => (
                <tr key={rule.signal}>
                  <td>
                    {rule.signal}
                  </td>

                  <td>
                    {(
                      rule.weight * 100
                    ).toFixed(2)}
                    %
                  </td>

                  <td>
                    <input
                      type="checkbox"
                      checked={
                        rule.included
                      }
                      onChange={() =>
                        handleToggle(
                          rule.signal
                        )
                      }
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <br />

          <button
            onClick={saveRule}
            disabled={saving}
          >
            {saving
              ? "Saving..."
              : "Save Rule"}
          </button>
        </>
      )}
    </div>
  );
}

export default RuleBuilder;