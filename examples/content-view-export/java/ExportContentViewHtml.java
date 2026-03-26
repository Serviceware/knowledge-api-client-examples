import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.file.Path;

/**
 * Exports a Serviceware Knowledge content view as a static HTML ZIP archive
 * using the REST API.
 *
 * <p>This example uses only the {@code java.net.http.HttpClient} shipped with
 * Java 11+ and has no external dependencies.</p>
 *
 * <p><strong>Prerequisites:</strong></p>
 * <ul>
 *   <li>Java 11 or later</li>
 *   <li>A Knowledge user account with the {@code BRANCH_EXPORT} permission</li>
 * </ul>
 *
 * <p><strong>Usage:</strong></p>
 * <pre>
 *   javac ExportContentViewHtml.java
 *   java ExportContentViewHtml
 * </pre>
 */
public class ExportContentViewHtml {

    // -----------------------------------------------------------------------
    // Configuration — adjust these values to match your environment
    // -----------------------------------------------------------------------
    private static final String BASE_URL = "https://<your-instance>/sabio-web/services";
    private static final String USERNAME = "<username>";
    private static final String PASSWORD = "<password>";
    private static final String CONTENT_VIEW_ID = "<content-view-id>";
    private static final String OUTPUT_FILE = "export.zip";

    public static void main(String[] args) throws IOException, InterruptedException {
        HttpClient client = HttpClient.newHttpClient();

        // Step 1: Authenticate and obtain a session token
        String token = authenticate(client);

        // Step 2: Export the content view and save to file
        exportContentView(client, token);
    }

    /**
     * Authenticates against the Knowledge REST API using credentials and
     * returns the session token.
     */
    private static String authenticate(HttpClient client) throws IOException, InterruptedException {
        System.out.println("Authenticating as '" + USERNAME + "'...");

        String requestBody = "{\"login\": \"" + USERNAME + "\", \"key\": \"" + PASSWORD + "\"}";

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(BASE_URL + "/authentication/credentials"))
                .header("Content-Type", "application/json; charset=utf-8")
                .POST(HttpRequest.BodyPublishers.ofString(requestBody))
                .build();

        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

        if (response.statusCode() != 200) {
            throw new RuntimeException("Authentication failed with HTTP " + response.statusCode()
                    + ": " + response.body());
        }

        // Extract the token from the JSON response.
        // The token is located at data.key in the response body.
        // Using simple string parsing to avoid external JSON library dependencies.
        String token = extractJsonValue(response.body(), "key");

        if (token == null || token.isEmpty()) {
            throw new RuntimeException("Authentication response did not contain a token. "
                    + "Response: " + response.body());
        }

        System.out.println("Authentication successful.");
        return token;
    }

    /**
     * Exports the content view as HTML and saves the resulting ZIP file.
     */
    private static void exportContentView(HttpClient client, String token)
            throws IOException, InterruptedException {

        System.out.println("Exporting content view " + CONTENT_VIEW_ID + " as HTML...");

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(BASE_URL + "/branch-export/" + CONTENT_VIEW_ID + "?type=html"))
                .header("sabio-auth-token", token)
                .GET()
                .build();

        HttpResponse<Path> response = client.send(request, HttpResponse.BodyHandlers.ofFile(Path.of(OUTPUT_FILE)));

        if (response.statusCode() != 200) {
            throw new RuntimeException("Export failed with HTTP " + response.statusCode()
                    + ". Check that the content view ID is valid and the user has the "
                    + "BRANCH_EXPORT permission.");
        }

        long fileSize = response.body().toFile().length();
        System.out.println("Export saved to '" + OUTPUT_FILE + "' (" + fileSize + " bytes).");
        System.out.println("Done.");
    }

    /**
     * Extracts a string value from a JSON response by searching for the last
     * occurrence of the given key. This simple approach avoids the need for a
     * JSON parsing library.
     *
     * <p>This works for flat or shallow JSON structures where the target key
     * has a string value. For production use, consider a proper JSON parser.</p>
     *
     * @param json the JSON string to search
     * @param key  the key whose value should be extracted
     * @return the extracted value, or {@code null} if the key was not found
     */
    private static String extractJsonValue(String json, String key) {
        // Search for the last occurrence of "key" to find the innermost/nested value
        // (e.g., data.key rather than a top-level key).
        String searchKey = "\"" + key + "\"";
        int keyIndex = json.lastIndexOf(searchKey);
        if (keyIndex < 0) {
            return null;
        }

        // Find the colon after the key
        int colonIndex = json.indexOf(':', keyIndex + searchKey.length());
        if (colonIndex < 0) {
            return null;
        }

        // Find the opening quote of the value
        int valueStart = json.indexOf('"', colonIndex + 1);
        if (valueStart < 0) {
            return null;
        }

        // Find the closing quote of the value
        int valueEnd = json.indexOf('"', valueStart + 1);
        if (valueEnd < 0) {
            return null;
        }

        return json.substring(valueStart + 1, valueEnd);
    }
}
