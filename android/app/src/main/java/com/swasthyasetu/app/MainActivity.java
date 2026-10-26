package com.swasthyasetu.app;

import android.app.Activity;
import android.os.Bundle;
import android.graphics.Color;
import android.view.Gravity;
import android.view.View;
import android.widget.*;
import org.json.JSONObject;

public class MainActivity extends Activity {
    LinearLayout root;
    EditText email, password, symptoms, duration, location;
    Spinner language;
    TextView status;
    String selectedLanguage = "en";

    int pad = 24;
    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        showLogin();
    }

    TextView text(String value, int size) {
        TextView t = new TextView(this); t.setText(value); t.setTextSize(size);
        t.setTextColor(Color.rgb(32, 48, 62)); t.setPadding(0, 8, 0, 8); return t;
    }
    Button button(String label, Runnable action) {
        Button b = new Button(this); b.setText(label); b.setOnClickListener(v -> action.run()); return b;
    }
    EditText edit(String hint, boolean multiline) {
        EditText e = new EditText(this); e.setHint(hint);
        if (multiline) { e.setMinLines(3); e.setGravity(Gravity.TOP); }
        return e;
    }
    void base(String title) {
        ScrollView scroll = new ScrollView(this);
        root = new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL); root.setPadding(pad,pad,pad,pad);
        root.setBackgroundColor(Color.rgb(246,249,251));
        root.addView(text("SwasthyaSetu", 28)); root.addView(text(title, 18));
        scroll.addView(root); setContentView(scroll);
    }
    void showLogin() {
        base("Bridging Care, Empowering Health");
        root.addView(text("Choose language / भाषा चुनें / भाषा निवडा", 14));
        language = new Spinner(this);
        String[] languages = {"English", "हिन्दी", "मराठी"};
        language.setAdapter(new ArrayAdapter<>(this, android.R.layout.simple_spinner_dropdown_item, languages));
        root.addView(language);
        email = edit("Email", false); root.addView(email);
        password = edit("Password", false); password.setInputType(129); root.addView(password);
        root.addView(button("Sign in", this::login));
        root.addView(button("Continue as demo patient (login required)", () -> {
            email.setText("patient@example.test"); password.setText("PatientDemo123!");
        }));
        status = text("Connect to the FastAPI backend to sign in.", 14); root.addView(status);
        root.addView(text("Emergency: if someone may be in immediate danger, call local emergency services directly. In India, call 112. Do not wait for this app.", 15));
    }
    void login() {
        try {
            selectedLanguage = language.getSelectedItemPosition() == 1 ? "hi" : language.getSelectedItemPosition() == 2 ? "mr" : "en";
            JSONObject body = new JSONObject(); body.put("email", email.getText().toString().trim());
            body.put("password", password.getText().toString());
            ApiClient.post("auth/login", body, (result, error) -> runOnUiThread(() -> {
                if (error != null) { status.setText("Sign-in failed: " + error.getMessage()); return; }
                try {
                    JSONObject json = new JSONObject(result); ApiClient.token = json.getString("access_token");
                    showHome(json.optString("display_name", "User"), json.optString("role", "patient"));
                } catch (Exception e) { status.setText("Could not read server response."); }
            }));
            status.setText("Signing in…");
        } catch (Exception e) { status.setText("Please check the entered details."); }
    }
    void showHome(String name, String role) {
        base("Welcome, " + name + " (" + role + ")");
        root.addView(text("Patient symptom assessment", 20));
        symptoms = edit("Describe symptoms (what is happening now?)", true); root.addView(symptoms);
        duration = edit("Duration (e.g. since this morning)", false); root.addView(duration);
        EditText allergies = edit("Known allergies (if any)", false); root.addView(allergies);
        root.addView(button("Check warning signs", () -> assess(allergies.getText().toString())));
        root.addView(text("Emergency support (simulation only)", 20));
        location = edit("Current location / landmark", false); root.addView(location);
        root.addView(button("Create simulated emergency request", this::emergency));
        root.addView(button("Sign out", () -> { ApiClient.token = ""; showLogin(); }));
        status = text("AI-generated notes and medication must be reviewed by a qualified clinician. This app does not dispatch an ambulance.", 14);
        root.addView(status);
    }
    void assess(String allergyText) {
        try {
            JSONObject body = new JSONObject(); body.put("symptoms", symptoms.getText().toString());
            body.put("duration", duration.getText().toString()); body.put("language", selectedLanguage);
            body.put("allergies", allergyText); body.put("current_medications", "");
            body.put("consent_to_ai_processing", false);
            ApiClient.post("triage", body, (result, error) -> runOnUiThread(() -> {
                if (error != null) { status.setText("Could not screen symptoms: " + error.getMessage()); return; }
                try {
                    JSONObject json = new JSONObject(result);
                    status.setText((json.optBoolean("possible_warning_sign") ? "POSSIBLE WARNING SIGN
" : "") +
                        json.optString("message") + "

" + json.optString("disclaimer"));
                } catch (Exception e) { status.setText(result); }
            }));
            status.setText("Checking configured warning signs…");
        } catch (Exception e) { status.setText("Enter symptoms first."); }
    }
    void emergency() {
        try {
            JSONObject body = new JSONObject(); body.put("symptoms", symptoms.getText().toString());
            body.put("location_text", location.getText().toString()); body.put("callback", "");
            body.put("symptoms_happening_now", true);
            ApiClient.post("emergency-requests", body, (result, error) -> runOnUiThread(() -> {
                if (error != null) { status.setText("Could not create simulation: " + error.getMessage()); return; }
                try { status.setText(new JSONObject(result).optString("warning")); }
                catch (Exception e) { status.setText(result); }
            }));
            status.setText("Creating simulated request…");
        } catch (Exception e) { status.setText("Please enter symptoms and location."); }
    }
}
