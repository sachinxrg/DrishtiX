package com.drishtix.controller;

import com.drishtix.model.TargetCategory;
import com.drishtix.model.TargetRegistry;
import com.drishtix.service.DnnFaceRecognitionService;
import com.drishtix.service.TargetRegistryService;
import java.util.concurrent.CompletableFuture;
import javafx.application.Platform;
import javafx.beans.binding.Bindings;
import javafx.collections.FXCollections;
import javafx.collections.ObservableList;
import javafx.fxml.FXML;
import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.Node;
import javafx.scene.control.*;
import javafx.scene.control.cell.PropertyValueFactory;
import javafx.scene.image.Image;
import javafx.scene.image.ImageView;
import javafx.scene.layout.GridPane;
import javafx.scene.layout.HBox;
import javafx.scene.layout.VBox;
import javafx.scene.paint.ImagePattern;
import javafx.scene.shape.Circle;
import javafx.stage.FileChooser;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;

/**
 * Controller for the full Target Registry management view.
 * Provides target table, search/filter, add, edit, and deactivate.
 * <p>
 * Bug fixes applied:
 * - Serial number stability on scroll/filter
 * - Profile image cell text leak on recycle
 * - NPE guard on null profileImagePath
 * - Category badge rendering instead of raw enum
 * - Scene null guard on file chooser
 * - Description tooltip on hover
 * - Status column with active/inactive badge
 * - Whitespace-only search query handling
 * - Registration dialog required-field validation
 * </p>
 */
public class RegistryController {

    private static final Logger log = LoggerFactory.getLogger(RegistryController.class);

    @FXML private TableView<TargetRegistry> targetTable;
    @FXML private TableColumn<TargetRegistry, Integer> colId;
    @FXML private TableColumn<TargetRegistry, String> colName;
    @FXML private TableColumn<TargetRegistry, String> colProfile;
    @FXML private TableColumn<TargetRegistry, TargetCategory> colCategory;
    @FXML private TableColumn<TargetRegistry, String> colStatus;
    @FXML private TableColumn<TargetRegistry, String> colCaseNumber;
    @FXML private TableColumn<TargetRegistry, String> colDescription;
    @FXML private TableColumn<TargetRegistry, LocalDateTime> colCreatedAt;
    @FXML private TextField searchField;
    @FXML private ComboBox<String> categoryFilter;
    
    // Bento Grid Panel UI
    @FXML private VBox emptyStatePanel;
    @FXML private VBox detailsPanel;
    @FXML private Circle profileAvatar;
    @FXML private Label recordCountLabel;
    @FXML private Label previewName;
    @FXML private Label previewCategory;
    @FXML private Label previewCase;
    @FXML private Label previewStatus;
    @FXML private TextArea previewDescription;

    private final TargetRegistryService registryService = TargetRegistryService.getInstance();
    private final ObservableList<TargetRegistry> targetList = FXCollections.observableArrayList();

    @FXML
    public void initialize() {
        setupTableColumns();
        setupCategoryFilter();
        setupSearchListener();
        setupRowSelection();

        if (targetTable != null) {
            targetTable.setItems(targetList);
        }

        loadTargets();
    }

    // ==================== Table Column Setup ====================

    private void setupTableColumns() {
        // --- BUG 1 FIX: Serial Number with stable index binding ---
        if (colId != null) {
            colId.setCellValueFactory(new PropertyValueFactory<>("targetId"));
            colId.setCellFactory(column -> new TableCell<TargetRegistry, Integer>() {
                @Override
                protected void updateItem(Integer item, boolean empty) {
                    super.updateItem(item, empty);
                    if (empty || getTableRow() == null || getTableRow().getItem() == null) {
                        setText(null);
                        setGraphic(null);
                    } else {
                        setText(String.valueOf(getIndex() + 1));
                        setStyle("-fx-alignment: CENTER; -fx-font-weight: bold; -fx-text-fill: #94A3B8;");
                    }
                }
            });
        }

        // --- Name column ---
        if (colName != null) {
            colName.setCellValueFactory(new PropertyValueFactory<>("fullName"));
            colName.setCellFactory(column -> new TableCell<TargetRegistry, String>() {
                @Override
                protected void updateItem(String name, boolean empty) {
                    super.updateItem(name, empty);
                    if (empty || name == null) {
                        setText(null);
                        setGraphic(null);
                    } else {
                        setText(name);
                        setStyle("-fx-font-weight: bold; -fx-text-fill: #1E293B;");
                    }
                }
            });
        }

        // --- BUG 4 FIX: Category column with colored badge ---
        if (colCategory != null) {
            colCategory.setCellValueFactory(new PropertyValueFactory<>("category"));
            colCategory.setCellFactory(column -> new TableCell<TargetRegistry, TargetCategory>() {
                @Override
                protected void updateItem(TargetCategory cat, boolean empty) {
                    super.updateItem(cat, empty);
                    setText(null);
                    if (empty || cat == null) {
                        setGraphic(null);
                    } else {
                        Label badge = new Label();
                        if (cat == TargetCategory.CRIMINAL) {
                            badge.setText("🔴 Criminal");
                            badge.getStyleClass().add("category-badge-criminal");
                        } else {
                            badge.setText("🔵 Missing Person");
                            badge.getStyleClass().add("category-badge-missing");
                        }
                        badge.getStyleClass().add("category-badge");
                        setGraphic(badge);
                    }
                }
            });
        }

        // --- BUG 7 FIX: Status column with active/inactive badge ---
        if (colStatus != null) {
            colStatus.setCellValueFactory(cellData -> {
                boolean active = cellData.getValue().isActive();
                return new javafx.beans.property.SimpleStringProperty(active ? "Active" : "Inactive");
            });
            colStatus.setCellFactory(column -> new TableCell<TargetRegistry, String>() {
                @Override
                protected void updateItem(String status, boolean empty) {
                    super.updateItem(status, empty);
                    setText(null);
                    if (empty || status == null) {
                        setGraphic(null);
                    } else {
                        Label badge = new Label(status);
                        if ("Active".equals(status)) {
                            badge.getStyleClass().addAll("status-badge", "status-active");
                        } else {
                            badge.getStyleClass().addAll("status-badge", "status-inactive");
                        }
                        setGraphic(badge);

                        // Dim the entire row if inactive
                        TableRow<?> row = getTableRow();
                        if (row != null) {
                            row.setOpacity("Active".equals(status) ? 1.0 : 0.55);
                        }
                    }
                }
            });
        }

        // --- Case Number column ---
        if (colCaseNumber != null) {
            colCaseNumber.setCellValueFactory(new PropertyValueFactory<>("caseNumber"));
        }

        // --- BUG 6 FIX: Description column with tooltip ---
        if (colDescription != null) {
            colDescription.setCellValueFactory(new PropertyValueFactory<>("description"));
            colDescription.setCellFactory(column -> new TableCell<TargetRegistry, String>() {
                @Override
                protected void updateItem(String desc, boolean empty) {
                    super.updateItem(desc, empty);
                    if (empty || desc == null || desc.isBlank()) {
                        setText(null);
                        setTooltip(null);
                        setGraphic(null);
                    } else {
                        // Truncate display to first 40 chars
                        String display = desc.length() > 40 ? desc.substring(0, 40) + "…" : desc;
                        setText(display);
                        setTooltip(new Tooltip(desc));
                        setStyle("-fx-text-fill: #64748B;");
                    }
                }
            });
        }

        // --- BUG 2 FIX: Profile Image column with setText(null) on recycle ---
        if (colProfile != null) {
            colProfile.setCellValueFactory(new PropertyValueFactory<>("profileImagePath"));
            colProfile.setCellFactory(column -> new TableCell<TargetRegistry, String>() {
                @Override
                protected void updateItem(String imagePath, boolean empty) {
                    super.updateItem(imagePath, empty);
                    setText(null); // BUG 2 FIX: always clear text
                    if (empty || imagePath == null || imagePath.isBlank()) {
                        setGraphic(null);
                    } else {
                        try {
                            File imgFile = new File(imagePath);
                            if (imgFile.exists()) {
                                ImageView imageView = new ImageView(
                                        new Image(imgFile.toURI().toString(), 44, 44, true, true));
                                imageView.setFitWidth(44);
                                imageView.setFitHeight(44);
                                Circle clip = new Circle(22, 22, 22);
                                imageView.setClip(clip);
                                imageView.setStyle("-fx-effect: dropshadow(gaussian, rgba(0,0,0,0.12), 4, 0, 0, 1);");
                                setGraphic(imageView);
                            } else {
                                // Fallback avatar
                                Label avatar = new Label("👤");
                                avatar.setStyle("-fx-font-size: 22; -fx-alignment: CENTER;");
                                setGraphic(avatar);
                            }
                        } catch (Exception e) {
                            Label avatar = new Label("👤");
                            avatar.setStyle("-fx-font-size: 22;");
                            setGraphic(avatar);
                        }
                    }
                }
            });
        }

        // --- Custom rendering for FIR Date ---
        if (colCreatedAt != null) {
            colCreatedAt.setCellValueFactory(new PropertyValueFactory<>("createdAt"));
            DateTimeFormatter formatter = DateTimeFormatter.ofPattern("dd/MM/yyyy");
            colCreatedAt.setCellFactory(column -> new TableCell<TargetRegistry, LocalDateTime>() {
                @Override
                protected void updateItem(LocalDateTime date, boolean empty) {
                    super.updateItem(date, empty);
                    if (empty || date == null) {
                        setText(null);
                        setGraphic(null);
                    } else {
                        setText(formatter.format(date));
                        setStyle("-fx-text-fill: #94A3B8; -fx-font-size: 11;");
                    }
                }
            });
        }
    }

    // ==================== Filter & Search ====================

    private void setupCategoryFilter() {
        if (categoryFilter != null) {
            categoryFilter.getItems().addAll("All", "CRIMINAL", "MISSING_PERSON");
            categoryFilter.setValue("All");
            categoryFilter.setOnAction(e -> handleSearch());
        }
    }

    private void setupSearchListener() {
        if (searchField != null) {
            searchField.textProperty().addListener((obs, old, newVal) -> handleSearch());
        }
    }

    // ==================== Row Selection → Preview Panel ====================

    private void setupRowSelection() {
        if (targetTable != null) {
            targetTable.getSelectionModel().selectedItemProperty().addListener((obs, oldSelection, newSelection) -> {
                updatePreviewPanel(newSelection);
            });
        }
        
        // Initial state: Hidden details, visible empty state
        updatePreviewPanel(null);
    }

    /**
     * Updates the right-side profile preview panel with target metadata.
     */
    private void updatePreviewPanel(TargetRegistry selected) {
        if (selected == null) {
            if (emptyStatePanel != null) emptyStatePanel.setVisible(true);
            if (detailsPanel != null) detailsPanel.setVisible(false);
            if (profileAvatar != null) profileAvatar.setFill(null);
            return;
        }

        // Show Details, Hide Empty State
        if (emptyStatePanel != null) emptyStatePanel.setVisible(false);
        if (detailsPanel != null) detailsPanel.setVisible(true);

        // Populate Avatar using ImagePattern for flawless clipping
        if (profileAvatar != null) {
            String imgPath = selected.getProfileImagePath();
            if (imgPath != null && !imgPath.isBlank()) {
                try {
                    File imgFile = new File(imgPath);
                    if (imgFile.exists()) {
                        Image img = new Image(imgFile.toURI().toString());
                        profileAvatar.setFill(new ImagePattern(img));
                    } else {
                        profileAvatar.setFill(null);
                    }
                } catch (Exception e) {
                    log.warn("Could not load profile avatar", e);
                    profileAvatar.setFill(null);
                }
            } else {
                profileAvatar.setFill(null);
            }
        }

        // UX 4: Enhanced preview metadata
        if (previewName != null) {
            previewName.setText(selected.getFullName());
        }
        if (previewCategory != null) {
            previewCategory.getStyleClass().removeAll("category-badge-criminal", "category-badge-missing", "category-badge");
            if (selected.getCategory() == TargetCategory.CRIMINAL) {
                previewCategory.setText("🔴 Criminal");
                previewCategory.getStyleClass().addAll("category-badge", "category-badge-criminal");
            } else {
                previewCategory.setText("🔵 Missing Person");
                previewCategory.getStyleClass().addAll("category-badge", "category-badge-missing");
            }
        }
        if (previewCase != null) {
            previewCase.setText(selected.getCaseNumber() != null ? selected.getCaseNumber() : "N/A");
        }
        if (previewStatus != null) {
            previewStatus.setText(selected.isActive() ? "✅ Active" : "⛔ Inactive");
            previewStatus.setStyle(selected.isActive()
                    ? "-fx-text-fill: #10B981; -fx-font-weight: bold;"
                    : "-fx-text-fill: #94A3B8; -fx-font-weight: bold;");
        }
        if (previewDescription != null) {
            previewDescription.setText(selected.getDescription() != null ? selected.getDescription() : "No description provided.");
        }
    }

    // ==================== Action Handlers ====================

    @FXML
    public void handleSearch() {
        // BUG 8 FIX: Trim and treat blank as "show all"
        String rawQuery = searchField != null ? searchField.getText() : "";
        String query = rawQuery.trim();
        if (query.isEmpty()) query = null; // null = show all in DAO

        String catValue = categoryFilter != null ? categoryFilter.getValue() : "All";
        TargetCategory catFilter = "All".equals(catValue) ? null : TargetCategory.fromDbValue(catValue);

        List<TargetRegistry> results;
        if (query == null && catFilter == null) {
            results = registryService.getAllTargets();
        } else {
            results = registryService.searchTargets(query, catFilter);
        }
        targetList.setAll(results);
        updateRecordCount();
    }

    @FXML
    public void handleAddTarget() {
        FileChooser fc = new FileChooser();
        fc.setTitle("Upload Target Photo");
        fc.getExtensionFilters().add(new FileChooser.ExtensionFilter("Images", "*.jpg", "*.jpeg", "*.png"));

        // BUG 5 FIX: Null guard on getScene()
        javafx.stage.Window owner = null;
        if (targetTable != null && targetTable.getScene() != null) {
            owner = targetTable.getScene().getWindow();
        }
        File file = fc.showOpenDialog(owner);
        if (file == null) return;

        Dialog<TargetRegistry> dialog = createRegistrationDialog(file);
        dialog.showAndWait().ifPresent(target -> {
            loadTargets();
            CompletableFuture.runAsync(() -> DnnFaceRecognitionService.getInstance().rebuildGallery());
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

        if (!selected.isActive()) {
            showInfo("Target \"" + selected.getFullName() + "\" is already deactivated.");
            return;
        }

        Alert confirm = new Alert(Alert.AlertType.CONFIRMATION);
        confirm.setTitle("Deactivate Target");
        confirm.setContentText("Deactivate " + selected.getFullName() + "? They will no longer trigger alerts.");
        confirm.showAndWait().ifPresent(btn -> {
            if (btn == ButtonType.OK) {
                registryService.deactivateTarget(selected.getTargetId());
                loadTargets();
                CompletableFuture.runAsync(() -> DnnFaceRecognitionService.getInstance().rebuildGallery());
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
                            CompletableFuture.runAsync(() -> DnnFaceRecognitionService.getInstance().rebuildGallery());
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

    // ==================== Data Loading ====================

    private void loadTargets() {
        List<TargetRegistry> all = registryService.getAllTargets();
        Platform.runLater(() -> {
            targetList.setAll(all);
            updateRecordCount();
        });
    }

    /**
     * UX 2: Updates the record count label.
     */
    private void updateRecordCount() {
        if (recordCountLabel != null) {
            int total = targetList.size();
            long active = targetList.stream().filter(TargetRegistry::isActive).count();
            long criminals = targetList.stream()
                    .filter(t -> t.getCategory() == TargetCategory.CRIMINAL && t.isActive()).count();
            long missing = targetList.stream()
                    .filter(t -> t.getCategory() == TargetCategory.MISSING_PERSON && t.isActive()).count();

            recordCountLabel.setText(String.format(
                    "%d records  •  %d active  •  🔴 %d criminals  •  🔵 %d missing",
                    total, active, criminals, missing));
        }
    }

    // ==================== Registration Dialog ====================

    /**
     * BUG 9 FIX: Registration dialog with field validation.
     * OK button is disabled until required fields (Name, Case #) are populated.
     */
    private Dialog<TargetRegistry> createRegistrationDialog(File photoFile) {
        Dialog<TargetRegistry> dialog = new Dialog<>();
        dialog.setTitle("DrishtiX — Register Target");
        dialog.setHeaderText("📸 Register New Target");

        GridPane grid = new GridPane();
        grid.setHgap(14);
        grid.setVgap(12);
        grid.setPadding(new Insets(24));

        // Photo preview
        try {
            ImageView photoPreview = new ImageView(
                    new Image(photoFile.toURI().toString(), 120, 120, true, true));
            photoPreview.setFitWidth(120);
            photoPreview.setFitHeight(120);
            Circle clip = new Circle(60, 60, 60);
            photoPreview.setClip(clip);
            grid.add(photoPreview, 0, 0, 2, 1);
            GridPane.setHalignment(photoPreview, javafx.geometry.HPos.CENTER);
        } catch (Exception e) {
            log.warn("Could not preview photo in dialog", e);
        }

        TextField nameField = new TextField();
        nameField.setPromptText("Full Name (required)");
        nameField.setPrefWidth(280);

        ComboBox<TargetCategory> catBox = new ComboBox<>();
        catBox.getItems().addAll(TargetCategory.values());
        catBox.setValue(TargetCategory.CRIMINAL);
        catBox.setPrefWidth(280);

        TextField caseField = new TextField();
        caseField.setPromptText("Case/FIR Number (required)");
        caseField.setPrefWidth(280);

        TextArea descField = new TextArea();
        descField.setPromptText("Description (optional)");
        descField.setPrefRowCount(3);
        descField.setPrefWidth(280);

        grid.add(new Label("Name:"), 0, 1);    grid.add(nameField, 1, 1);
        grid.add(new Label("Category:"), 0, 2); grid.add(catBox, 1, 2);
        grid.add(new Label("Case #:"), 0, 3);   grid.add(caseField, 1, 3);
        grid.add(new Label("Description:"), 0, 4); grid.add(descField, 1, 4);

        dialog.getDialogPane().setContent(grid);
        dialog.getDialogPane().getButtonTypes().addAll(ButtonType.OK, ButtonType.CANCEL);

        // BUG 9 FIX: Disable OK button until required fields are filled
        Node okButton = dialog.getDialogPane().lookupButton(ButtonType.OK);
        okButton.setDisable(true);

        // Bind enable state to non-empty required fields
        nameField.textProperty().addListener((obs, old, val) ->
                okButton.setDisable(val.trim().isEmpty() || caseField.getText().trim().isEmpty()));
        caseField.textProperty().addListener((obs, old, val) ->
                okButton.setDisable(val.trim().isEmpty() || nameField.getText().trim().isEmpty()));

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

    // ==================== Utility ====================

    private void showInfo(String msg) {
        Platform.runLater(() -> {
            Alert a = new Alert(Alert.AlertType.INFORMATION);
            a.setTitle("DrishtiX");
            a.setContentText(msg);
            a.showAndWait();
        });
    }
}
