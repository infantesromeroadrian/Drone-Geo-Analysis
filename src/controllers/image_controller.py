#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Controlador principal para la herramienta de análisis geográfico de imágenes.
"""

import os
import sys
import logging
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Dict, Any, List, Optional
import json

from src.models.geo_analyzer import GeoAnalyzer
from src.utils.helpers import (
    encode_image_to_base64,
    get_image_metadata,
    format_geo_results,
    save_analysis_results
)

logger = logging.getLogger(__name__)

class ImageController:
    """
    Controlador para la gestión de imágenes y flujo de la aplicación.
    Implementa la interfaz de usuario y coordina la interacción entre
    los modelos de análisis y la visualización de resultados.
    """
    
    def __init__(self):
        """Inicializa el controlador de imágenes."""
        self.analyzer = GeoAnalyzer()
        self.current_image = None
        self.current_results = None
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz de usuario."""
        self.root = tk.Tk()
        self.root.title("Análisis Geográfico OSINT")
        self.root.geometry("900x600")
        self.root.minsize(800, 500)
        
        # Estilo
        self.style = ttk.Style()
        self.style.configure("TButton", padding=6, relief="flat", background="#4CAF50")
        self.style.configure("TLabel", font=('Arial', 11))
        self.style.configure("Header.TLabel", font=('Arial', 14, 'bold'))
        
        # Menú principal
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)
        
        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Archivo", menu=file_menu)
        file_menu.add_command(label="Abrir imagen", command=self.load_image)
        file_menu.add_command(label="Guardar resultados", command=self.save_results)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.root.quit)
        
        help_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Ayuda", menu=help_menu)
        help_menu.add_command(label="Acerca de", command=self.show_about)
        
        # Panel principal
        main_panel = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_panel.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Panel izquierdo (controles)
        left_frame = ttk.Frame(main_panel, width=200)
        main_panel.add(left_frame, weight=1)
        
        # Panel de controles
        control_frame = ttk.LabelFrame(left_frame, text="Controles")
        control_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Button(control_frame, text="Cargar imagen", command=self.load_image).pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(control_frame, text="Analizar imagen", command=self.analyze_current_image).pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(control_frame, text="Guardar resultados", command=self.save_results).pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(control_frame, text="Limpiar", command=self.clear_all).pack(fill=tk.X, padx=5, pady=5)
        
        # Información de la imagen
        self.image_info_frame = ttk.LabelFrame(left_frame, text="Información de la imagen")
        self.image_info_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.image_path_var = tk.StringVar()
        self.image_size_var = tk.StringVar()
        self.image_dim_var = tk.StringVar()
        
        ttk.Label(self.image_info_frame, text="Archivo:").pack(anchor=tk.W, padx=5, pady=2)
        ttk.Label(self.image_info_frame, textvariable=self.image_path_var).pack(anchor=tk.W, padx=5, pady=2)
        
        ttk.Label(self.image_info_frame, text="Tamaño:").pack(anchor=tk.W, padx=5, pady=2)
        ttk.Label(self.image_info_frame, textvariable=self.image_size_var).pack(anchor=tk.W, padx=5, pady=2)
        
        ttk.Label(self.image_info_frame, text="Dimensiones:").pack(anchor=tk.W, padx=5, pady=2)
        ttk.Label(self.image_info_frame, textvariable=self.image_dim_var).pack(anchor=tk.W, padx=5, pady=2)
        
        # Panel derecho (visualización)
        right_frame = ttk.Frame(main_panel)
        main_panel.add(right_frame, weight=3)
        
        # Visor de imagen
        self.image_frame = ttk.LabelFrame(right_frame, text="Imagen")
        self.image_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.image_canvas = tk.Canvas(self.image_frame, bg="white")
        self.image_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Resultados del análisis
        self.results_frame = ttk.LabelFrame(right_frame, text="Resultados del análisis")
        self.results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.results_tree = ttk.Treeview(self.results_frame, columns=("Valor", "Confianza"), show="headings")
        self.results_tree.heading("Valor", text="Valor")
        self.results_tree.heading("Confianza", text="Confianza")
        self.results_tree.column("Valor", width=300)
        self.results_tree.column("Confianza", width=100)
        self.results_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Barra de estado
        self.status_var = tk.StringVar()
        self.status_var.set("Listo. Cargue una imagen para comenzar el análisis.")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        logger.info("Interfaz de usuario inicializada")
    
    def run(self):
        """Inicia la ejecución de la aplicación."""
        logger.info("Iniciando la aplicación")
        self.root.mainloop()
    
    def load_image(self):
        """Abre un diálogo para cargar una imagen."""
        try:
            # Configurar directorio inicial (considerar USER_HOME para Docker)
            initial_dir = os.environ.get('USER_HOME', os.path.expanduser('~'))
            
            file_path = filedialog.askopenfilename(
                title="Seleccionar imagen",
                initialdir=initial_dir,
                filetypes=[
                    ("Imágenes", "*.jpg *.jpeg *.png *.bmp *.gif"),
                    ("Todos los archivos", "*.*")
                ]
            )
            
            if not file_path:
                return
            
            # Convertir ruta si estamos en Docker y la ruta es del host
            if os.environ.get('PYTHONPATH') == '/app' and not file_path.startswith('/app'):
                # Si el sistema de archivos del host está montado en /host
                if file_path.startswith('/'):
                    docker_path = f"/host{file_path}"
                    if os.path.exists(docker_path):
                        file_path = docker_path
                        logger.info(f"Ruta convertida para Docker: {file_path}")
            
            # Obtener metadatos de la imagen
            metadata = get_image_metadata(file_path)
            self.current_image = {
                "path": file_path,
                "metadata": metadata
            }
            
            # Actualizar información de la imagen
            self.image_path_var.set(os.path.basename(file_path))
            self.image_size_var.set(f"{metadata['size'] / 1024:.1f} KB")
            self.image_dim_var.set(f"{metadata['dimensions'][0]}x{metadata['dimensions'][1]}")
            
            # Mostrar la imagen
            self._display_image(file_path)
            
            self.status_var.set(f"Imagen cargada: {os.path.basename(file_path)}")
            logger.info(f"Imagen cargada: {file_path}")
            
        except Exception as e:
            logger.error(f"Error al cargar la imagen: {str(e)}")
            messagebox.showerror("Error", f"No se pudo cargar la imagen: {str(e)}")
            self.status_var.set("Error al cargar la imagen")
    
    def _display_image(self, image_path):
        """
        Muestra la imagen en el canvas.
        
        Args:
            image_path: Ruta a la imagen a mostrar
        """
        try:
            from PIL import Image, ImageTk
            
            # Cargar la imagen
            image = Image.open(image_path)
            
            # Obtener dimensiones del canvas
            canvas_width = self.image_canvas.winfo_width()
            canvas_height = self.image_canvas.winfo_height()
            
            # Si el canvas aún no tiene dimensiones (inicio), usar valores predeterminados
            if canvas_width <= 1 or canvas_height <= 1:
                canvas_width = 400
                canvas_height = 300
            
            # Ajustar dimensiones para que quepa en el canvas
            img_width, img_height = image.size
            ratio = min(canvas_width/img_width, canvas_height/img_height)
            
            # Si la relación es 0, usar un valor predeterminado
            if ratio <= 0:
                ratio = 0.5
            
            new_width = int(img_width * ratio)
            new_height = int(img_height * ratio)
            
            # Redimensionar la imagen
            image = image.resize((new_width, new_height), Image.LANCZOS)
            
            # Convertir a formato compatible con tkinter
            self.tk_image = ImageTk.PhotoImage(image)
            
            # Limpiar canvas y mostrar la imagen
            self.image_canvas.delete("all")
            self.image_canvas.create_image(
                canvas_width/2, canvas_height/2, 
                image=self.tk_image, anchor=tk.CENTER
            )
            
        except Exception as e:
            logger.error(f"Error al mostrar la imagen: {str(e)}")
            messagebox.showerror("Error", f"No se pudo mostrar la imagen: {str(e)}")
    
    def analyze_current_image(self):
        """Analiza la imagen actualmente cargada."""
        if not self.current_image:
            messagebox.showwarning("Advertencia", "Debe cargar una imagen primero")
            return
        
        try:
            self.status_var.set("Analizando imagen...")
            self.root.update()
            
            # Codificar la imagen a base64
            image_path = self.current_image["path"]
            base64_image = encode_image_to_base64(image_path)
            
            if not base64_image:
                raise ValueError("No se pudo codificar la imagen")
            
            # Realizar el análisis
            results = self.analyzer.analyze_image(base64_image, self.current_image["metadata"])
            
            # Formatear los resultados
            self.current_results = format_geo_results(results)
            
            # Mostrar los resultados
            self._display_results(self.current_results)
            
            self.status_var.set("Análisis completado")
            logger.info("Análisis de imagen completado")
            
        except Exception as e:
            logger.error(f"Error en el análisis: {str(e)}")
            messagebox.showerror("Error", f"No se pudo analizar la imagen: {str(e)}")
            self.status_var.set("Error en el análisis")
    
    def _display_results(self, results):
        """
        Muestra los resultados en el árbol de resultados.
        
        Args:
            results: Resultados del análisis
        """
        # Limpiar resultados anteriores
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # Insertar resultados nuevos
        location = results["location"]
        
        # Añadir la ubicación
        country_id = self.results_tree.insert("", "end", text="País", 
                     values=(location["country"], f"{results['confidence']}%"))
        
        city_id = self.results_tree.insert("", "end", text="Ciudad", 
                  values=(location["city"], ""))
        
        district_id = self.results_tree.insert("", "end", text="Distrito", 
                      values=(location["district"], ""))
        
        neighborhood_id = self.results_tree.insert("", "end", text="Barrio", 
                          values=(location["neighborhood"], ""))
        
        street_id = self.results_tree.insert("", "end", text="Calle", 
                    values=(location["street"], ""))
        
        # Añadir evidencia
        if "supporting_evidence" in results and results["supporting_evidence"]:
            evidence_id = self.results_tree.insert("", "end", text="Evidencia", values=("", ""))
            
            for i, evidence in enumerate(results["supporting_evidence"]):
                self.results_tree.insert(evidence_id, "end", text=f"Elemento {i+1}", 
                                        values=(evidence, ""))
        
        # Añadir alternativas
        if "possible_alternatives" in results and results["possible_alternatives"]:
            alt_id = self.results_tree.insert("", "end", text="Alternativas", values=("", ""))
            
            for i, alt in enumerate(results["possible_alternatives"]):
                alt_item = self.results_tree.insert(alt_id, "end", text=f"Alternativa {i+1}", 
                                                  values=(f"{alt['country']}, {alt['city']}", 
                                                          f"{alt['confidence']}%"))
    
    def save_results(self):
        """Guarda los resultados del análisis."""
        if not self.current_results or not self.current_image:
            messagebox.showwarning("Advertencia", "No hay resultados para guardar")
            return
        
        try:
            # Guardar los resultados
            output_path = save_analysis_results(self.current_results, self.current_image["path"])
            
            if output_path:
                messagebox.showinfo("Información", f"Resultados guardados en {output_path}")
                self.status_var.set(f"Resultados guardados en {os.path.basename(output_path)}")
            else:
                messagebox.showwarning("Advertencia", "No se pudieron guardar los resultados")
                
        except Exception as e:
            logger.error(f"Error al guardar los resultados: {str(e)}")
            messagebox.showerror("Error", f"No se pudieron guardar los resultados: {str(e)}")
            self.status_var.set("Error al guardar los resultados")
    
    def clear_all(self):
        """Limpia la imagen y los resultados."""
        self.current_image = None
        self.current_results = None
        
        # Limpiar la información de la imagen
        self.image_path_var.set("")
        self.image_size_var.set("")
        self.image_dim_var.set("")
        
        # Limpiar la imagen
        self.image_canvas.delete("all")
        
        # Limpiar los resultados
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        self.status_var.set("Listo. Cargue una imagen para comenzar el análisis.")
        logger.info("Interfaz limpiada")
    
    def show_about(self):
        """Muestra información sobre la aplicación."""
        about_text = """
        Herramienta de Análisis Geográfico OSINT
        
        Esta aplicación utiliza visión artificial y GPT-4 para analizar 
        imágenes y determinar su ubicación geográfica basándose en 
        características visibles como arquitectura, carteles, vegetación,
        personas, vehículos y estructura urbana.
        
        Uso militar y de inteligencia.
        """
        messagebox.showinfo("Acerca de", about_text) 