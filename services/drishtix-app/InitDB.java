import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.Statement;
import java.nio.file.Files;
import java.nio.file.Paths;

public class InitDB {
    public static void main(String[] args) {
        String url = "jdbc:mysql://localhost:3306/?useSSL=false&serverTimezone=UTC&allowPublicKeyRetrieval=true";
        String user = "root";
        String password = "";
        
        try (Connection conn = DriverManager.getConnection(url, user, password);
             Statement stmt = conn.createStatement()) {
            
            System.out.println("Connected to MySQL server!");
            
            // Read schema file
            String schema = new String(Files.readAllBytes(Paths.get("../../database/drishtix_schema.sql")));
            String[] queries = schema.split(";");
            
            for (String query : queries) {
                if (query.trim().length() > 0) {
                    stmt.execute(query);
                }
            }
            
            System.out.println("Database and schema initialized successfully!");
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
