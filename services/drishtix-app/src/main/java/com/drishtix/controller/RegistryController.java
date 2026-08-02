package com.drishtix.controller;

import com.drishtix.model.TargetCategory;
import com.drishtix.model.TargetRegistry;
import com.drishtix.service.TargetRegistryService;
import javafx.application.Platform;
import javafx.collections.FXCollections;
import javafx.collections.ObservableList;
import javafx.fxml.FXML;
import javafx.geometry.Insets;
import javafx.scene.control.*;
import javafx.scene.control.cell.PropertyValueFactory;
import javafx.scene.image.Image;
import javafx.scene.image.ImageView;
import javafx.scene.layout.GridPane;
import javafx.stage.FileChooser;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import javafx.scene.shape.Circle;
import javafx.beans.property.SimpleStringProperty;

/**
 * Controller for the full Target Registry management view.
 * Provides target table, search/filter, add, edit, and deactivate.
 */
public class RegistryController {

    private static final Logger log = LoggerFactory.getLogger(RegistryController.class);

    @FXML private TableView<TargetRegistry> targetTable;
    @FXML private TableColumn<TargetRegistry, Integer> colId;
    @FXML private TableColumn<TargetRegistry, String> colName;
    @FXML private TableColumn<TargetRegistry, String> colProfile;
    @FXML private TableColumn<TargetRegistry, TargetCategory> colCategory;
    @FXML private TableColumn<TargetRegistry, String> colCaseNumber;
    @FXML private TableColumn<TargetRegistry, String> colDescription;
    @FXML private TableColumn<TargetRegistry, LocalDateTime> colCreatedAt;
    @FXML private TextField searchField;
    @FXML private ComboBox<String> categoryFilter;
    @FXML private ImageView profilePreview;

    private final TargetRegistryService registryService = TargetRegistryService.getInstance();
    private final ObservableList<TargetRegistry> targetList = FXCollections.observableArrayList();

    @FXML
    public void initialize() {
        // Set up table columns
        if (colId != null) colId.setCellValueFactory(new PropertyValueFactory<>("targetId"));
        if (colName != null) colName.setCellValueFactory(new PropertyValueFactory<>("fullName"));
        if (colCategory != null) colCategory.setCellValueFactory(new PropertyValueFactory<>("category"));
        if (colCaseNumber != null) colCaseNumber.setCellValueFactory(new PropertyValueFactory<>("caseNumber"));
        if (colDescription != null) colDescription.setCellValueFactory(new PropertyValueFactory<>("description"));
        
        // Custom rendering for Profile image
        if (colProfile != null) {
            colProfile.setCellValueFactory(new PropertyValueFactory<>("profileImagePath"));
            colProfile.setCellFactory(column -> new TableCell<TargetRegistry, String>() {
                @Override
                protected void updateItem(String imagePath, boolean empty) {
                    super.updateItem(imagePath, empty);
                    if (empty || imagePath == null) {
                        setGraphic(null);
                    } else {
                        try {
                            File imgFile = new File(imagePath);
                            if (imgFile.exists()) {
                                ImageView imageView = new ImageView(new Image(imgFile.toURI().toString(), 40, 40, true, true));
                                // Make it a circle
                                Circle clip = new Circle(20, 20, 20);
                                imageView.setClip(clip);
                                setGraphic(imageView);
                            } else {
                                setGraphic(null);
                            }
                        } catch (Exception e) {
                            setGraphic(null);
                        }
                    }
                }
            });
        }

        // Custom rendering for Date of FIR
        if (colCreatedAt != null) {
            colCreatedAt.setCellValueFactory(new PropertyValueFactory<>("createdAt"));
            DateTimeFormatter formatter = DateTimeFormatter.ofPattern("dd/MM/yyyy");
            colCreatedAt.setCellFactory(column -> new TableCell<TargetRegistry, LocalDateTime>() {
                @Override
                protected void updateItem(LocalDateTime date, boolean empty) {
                    super.updateItem(date, empty);
                    if (empty || date == null) {
                        setText(null);
                    } else {
                        setText(formatter.format(date));
                    }
                }
            });
        }

        // Category filter
        if (categoryFilter != null) {
            categoryFilter.getItems().addAll("All", "CRIMINAL", "MISSING_PERSON");
            categoryFilter.setValue("All");
            categoryFilter.setOnAction(e -> handleSearch());
        }

        // Search listener
        if (searchField != null) {
            searchField.textProperty().addListener((obs, old, newVal) -> handleSearch());
        }

        // Row selection → show profile image
        if (targetTable != null) {
            targetTable.setItems(targetList);
            targetTable.getSelectionModel().selectedItemProperty().addListener((obs, old, selected) -> {
                if (selected != null && profilePreview != null) {
                    try {
                        File imgFile = new File(selected.getProfileImagePath());
                        if (imgFile.exists()) {
                            profilePreview.setImage(new Image(imgFile.toURI().toString(), 200, 200, true, true));
                        }
                    } catch (Exception e) {
                        log.warn("Could not load profile preview", e);
                    }
                }
            });
        }

        loadTargets();
    }

    @FXML
    public void handleSearch() {
        String query = searchField != null ? searchField.getText() : "";
        String catValue = categoryFilter != null ? categoryFilter.getValue() : "All";
        TargetCategory catFilter = "All".equals(catValue) ? null : TargetCategory.fromDbValue(catValue);

        List<TargetRegistry> results = registryService.searchTargets(query, catFilter);
        targetList.setAll(results);
    }

    @FXML
    public void handleAddTarget() {
        FileChooser fc = new FileChooser();
        fc.setTitle("Upload Target Photo");
        fc.getExtensionFilters().add(new FileChooser.ExtensionFilter("Images", "*.jpg", "*.jpeg", "*.png"));
        File file = fc.showOpenDialog(targetTable.getScene().getWindow());
        if (file == null) return;

        Dialog<TargetRegistry> dialog = createRegistrationDialog(file);
        dialog.showAndWait().ifPresent(target -> {
            loadTargets();
            showInfo("Target registered: " + target.getFullName());
        });
    }

    @FXML
    public void handleDeactivate() {
        TargetRegistry selected = targetTable.getSelectionModel().getSelectedItem();
        if (selected == null) {
            showInfo("Please select a target to deactivate.");
            return;
        }

        Alert confirm = new Alert(Alert.AlertType.CONFIRMATION);
        confirm.setTitle("Deactivate Target");
        confirm.setContentText("Deactivate " + selected.getFullName() + "? They will no longer trigger alerts.");
        confirm.showAndWait().ifPresent(btn -> {
            if (btn == ButtonType.OK) {
                registryService.deactivateTarget(selected.getTargetId());
                loadTargets();
            }
        });
    }

    @FXML
    public void handleDeleteTarget() {
        TargetRegistry selected = targetTable.getSelectionModel().getSelectedItem();
        if (selected == null) {
            showInfo("Please select a target to delete.");
            return;
        }

        // Step 1: Initial warning
        Alert warning = new Alert(Alert.AlertType.WARNING);
        warning.setTitle("Delete Target — Warning");
        warning.setHeaderText("⚠ Permanent Deletion");
        warning.setContentText(
                "You are about to permanently delete:\n\n" +
                "  Target: " + selected.getFullName() + "\n" +
                "  Case #: " + selected.getCaseNumber() + "\n" +
                "  Category: " + selected.getCategory() + "\n\n" +
                "This will also delete ALL associated:\n" +
                "  • Uploaded photos & face templates\n" +
                "  • Detection log entries & snapshots\n\n" +
                "This action CANNOT be undone. Continue?");
        warning.getButtonTypes().setAll(ButtonType.YES, ButtonType.CANCEL);

        warning.showAndWait().ifPresent(btn -> {
            if (btn == ButtonType.YES) {
                // Step 2: Final confirmation
                Alert finalConfirm = new Alert(Alert.AlertType.CONFIRMATION);
                finalConfirm.setTitle("Final Confirmation");
                finalConfirm.setHeaderText("🗑️ Last Chance");
                finalConfirm.setContentText(
                        "Are you absolutely sure you want to permanently delete \"" +
                        selected.getFullName() + "\"?");
                finalConfirm.getButtonTypes().setAll(ButtonType.OK, ButtonType.CANCEL);

                finalConfirm.showAndWait().ifPresent(finalBtn -> {
                    if (finalBtn == ButtonType.OK) {
                        try {
                            registryService.deleteTarget(selected.getTargetId());
                            loadTargets();
                            showInfo("Target \"" + selected.getFullName() + "\" has been permanently deleted.");
                        } catch (Exception e) {
                            log.error("Failed to delete target: {}", selected.getTargetId(), e);
                            Platform.runLater(() -> {
                                Alert error = new Alert(Alert.AlertType.ERROR);
                                error.setTitle("Delete Failed");
                                error.setContentText("Failed to delete target: " + e.getMessage());
                                error.showAndWait();
                            });
                        }
                    }
                });
            }
        });
    }

    @FXML
    public void handleRefresh() {
        loadTargets();
    }

    private void loadTargets() {
        List<TargetRegistry> all = registryService.getAllTargets();
        Platform.runLater(() -> targetList.setAll(all));
    }

    private Dialog<TargetRegistry> createRegistrationDialog(File photoFile) {
        Dialog<TargetRegistry> dialog = new Dialog<>();
        dialog.setTitle("DrishtiX — Register Target");

        GridPane grid = new GridPane();
        grid.setHgap(10);
        grid.setVgap(10);
        grid.setPadding(new Insets(20));

        TextField nameField = new TextField();
        nameField.setPromptText("Full Name");
        ComboBox<TargetCategory> catBox = new ComboBox<>();
        catBox.getItems().addAll(TargetCategory.values());
        catBox.setValue(TargetCategory.CRIMINAL);
        TextField caseField = new TextField();
        caseField.setPromptText("Case/FIR Number");
        TextArea descField = new TextArea();
        descField.setPromptText("Description");
        descField.setPrefRowCount(2);

        grid.add(new Label("Name:"), 0, 0);   grid.add(nameField, 1, 0);
        grid.add(new Label("Category:"), 0, 1); grid.add(catBox, 1, 1);
        grid.add(new Label("Case #:"), 0, 2);  grid.add(caseField, 1, 2);
        grid.add(new Label("Desc:"), 0, 3);    grid.add(descField, 1, 3);

        dialog.getDialogPane().setContent(grid);
        dialog.getDialogPane().getButtonTypes().addAll(ButtonType.OK, ButtonType.CANCEL);

        dialog.setResultConverter(btn -> {
            if (btn == ButtonType.OK) {
                try {
                    return registryService.registerTarget(
                            photoFile.getAbsolutePath(),
                            nameField.getText().trim(),
                            catBox.getValue(),
                            caseField.getText().trim(),
                            descField.getText().trim());
                } catch (Exception e) {
                    showInfo("Error: " + e.getMessage());
                }
            }
            return null;
        });

        return dialog;
    }

    private void showInfo(String msg) {
        Platform.runLater(() -> {
            Alert a = new Alert(Alert.AlertType.INFORMATION);
            a.setTitle("DrishtiX");
            a.setContentText(msg);
            a.showAndWait();
        });
    }
}
