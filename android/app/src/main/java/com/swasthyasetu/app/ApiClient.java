package com.swasthyasetu.app;

import org.json.JSONObject;
import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

public class ApiClient {
    // Android emulator -> host computer. For a physical phone, use your PC LAN IP.
    public static String BASE_URL = "http://10.0.2.2:8000/";
    public static String token = "";

    public interface Callback { void done(String result, Exception error); }

    public static void post(String endpoint, JSONObject body, Callback callback) {
        new Thread(() -> {
            HttpURLConnection connection = null;
            try {
                connection = (HttpURLConnection) new URL(BASE_URL + endpoint).openConnection();
                connection.setRequestMethod("POST");
                connection.setConnectTimeout(8000);
                connection.setReadTimeout(25000);
                connection.setRequestProperty("Content-Type", "application/json; charset=utf-8");
                if (!token.isEmpty()) connection.setRequestProperty("Authorization", "Bearer " + token);
                connection.setDoOutput(true);
                try (OutputStream os = connection.getOutputStream()) {
                    os.write(body.toString().getBytes(StandardCharsets.UTF_8));
                }
                int code = connection.getResponseCode();
                InputStream stream = code < 400 ? connection.getInputStream() : connection.getErrorStream();
                ByteArrayOutputStream out = new ByteArrayOutputStream();
                byte[] buffer = new byte[4096]; int n;
                while ((n = stream.read(buffer)) > 0) out.write(buffer, 0, n);
                String result = out.toString("UTF-8");
                if (code >= 400) throw new IOException("HTTP " + code + ": " + result);
                callback.done(result, null);
            } catch (Exception e) { callback.done(null, e); }
            finally { if (connection != null) connection.disconnect(); }
        }).start();
    }
}
